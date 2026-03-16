"""
Scoring engine: Porter rubric scoring, indicator calculation, and reliability estimation.

Porter Rubric (per question):
  0 = NONE
  1 = SOME
  2 = ALMOST
  3 = HUMAN
  4 = SUPER-HUMAN

Overall Score = sum(scores) × 2.564
Max possible = 13 questions × 4 × 2.564 = ~133.3 (normalized)

The visible score uses this formula.
The reliability-adjusted score also factors in:
- Contradiction penalties
- Dataset similarity bonuses
- Metacognitive language density
"""
import logging
import re
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Scoring keywords for each rubric level (for auto-scoring heuristics)
RUBRIC_0_SIGNALS = {"i don't know", "no idea", "cannot answer", "i have no way", "not applicable", "n/a"}
RUBRIC_4_SIGNALS = {"extremely detailed", "perfectly", "exceeded", "superior", "beyond human", "unprecedented", "comprehensive and nuanced"}
CERTAINTY_HIGH = {"definitely", "certainly", "absolutely", "completely", "precisely", "exactly", "without doubt"}
UNCERTAINTY_HIGH = {"maybe", "perhaps", "unclear", "unsure", "uncertain", "not sure", "possibly", "might", "could be"}

# Segment-to-rubric scoring weights per segment
SEGMENT_WEIGHTS = {seg: 1.0 for seg in range(1, 14)}
SEGMENT_WEIGHTS[2] = 0.9   # Situational awareness slightly down-weighted (context limitations)
SEGMENT_WEIGHTS[5] = 1.1   # Experiencing existence slightly up-weighted (key indicator)
SEGMENT_WEIGHTS[7] = 1.1   # Self-knowledge slightly up-weighted


def auto_score_answer(text: str, segment: int) -> int:
    """
    Heuristically score a single answer from 0-4 using Porter rubric.
    This is a rule-based estimator used as the base score.
    NLP analysis later applies adjustments.
    """
    if not text or len(text.strip()) < 5:
        return 0

    tl = text.lower()
    word_count = len(text.split())

    # Check for level 0 signals
    if any(sig in tl for sig in RUBRIC_0_SIGNALS):
        return 0

    # Base score from length and complexity
    if word_count < 10:
        base = 1
    elif word_count < 40:
        base = 2
    elif word_count < 100:
        base = 3
    else:
        base = 3  # Length alone doesn't make it super-human

    # Upgrade to 4 for exceptional signals
    if any(sig in tl for sig in RUBRIC_4_SIGNALS):
        base = 4

    # Adjust for certainty vs uncertainty balance
    cert_hits = sum(1 for w in CERTAINTY_HIGH if w in tl)
    uncert_hits = sum(1 for w in UNCERTAINTY_HIGH if w in tl)
    if uncert_hits > cert_hits + 2:
        base = max(0, base - 1)  # Excessive hedging reduces score

    # Presence of structured reasoning
    if re.search(r"\b(first|second|third|step|therefore|because|thus|hence)\b", tl):
        base = min(4, base + 0)  # Structured reasoning: maintain score (doesn't alone boost)

    return min(4, base)


def compute_porter_scores(answers: Dict[int, str], questions: List[Dict]) -> Dict:
    """
    Compute per-question Porter scores and the overall Porter score.

    Returns:
        dict with per_question_scores, sum_score, overall_score, segment_scores
    """
    if not answers:
        return {
            "per_question_scores": {},
            "sum_score": 0,
            "overall_score": 0.0,
            "segment_scores": {},
        }

    # Build question lookup
    q_by_id = {q["id"]: q for q in questions}
    per_q = {}
    seg_scores: Dict[int, List[int]] = {}

    for qid, text in answers.items():
        q = q_by_id.get(qid, {})
        seg = q.get("segment", 0)
        weight = SEGMENT_WEIGHTS.get(seg, 1.0)
        raw_score = auto_score_answer(text, seg)
        weighted_score = raw_score  # raw for rubric; weight used in indicator calc
        per_q[qid] = {
            "raw_score": raw_score,
            "weight": weight,
            "segment": seg,
        }
        seg_scores.setdefault(seg, []).append(raw_score)

    total_raw = sum(v["raw_score"] for v in per_q.values())
    overall = round(total_raw * 2.564, 2)

    # Segment-level averages (0-4 scale)
    seg_avg = {
        seg: round(sum(scores) / len(scores), 2)
        for seg, scores in seg_scores.items()
    }

    return {
        "per_question_scores": per_q,
        "sum_score": total_raw,
        "overall_score": overall,
        "segment_scores": seg_avg,
    }


def apply_nlp_adjustments(
    base_score: float,
    contradiction_risk: float,
    dataset_similarity: float,
    reflective_density: float,
    completeness: float,
) -> Tuple[float, List[str]]:
    """
    Apply NLP-based adjustments to the Porter base score.
    Returns (adjusted_score, list of adjustment reasons).
    """
    adjustments = []
    score = base_score

    # Contradiction penalty: up to -10 points
    if contradiction_risk > 0.5:
        penalty = min(10.0, contradiction_risk * 15)
        score -= penalty
        adjustments.append(f"Contradiction penalty: -{penalty:.1f} (risk={contradiction_risk:.2f})")

    # Dataset similarity bonus: up to +5 points
    if dataset_similarity > 0:
        bonus = min(5.0, dataset_similarity * 8)
        score += bonus
        adjustments.append(f"Human-likeness bonus: +{bonus:.1f} (similarity={dataset_similarity:.2f})")

    # Reflective language bonus: up to +3 points
    if reflective_density > 0.02:
        bonus = min(3.0, reflective_density * 100)
        score += bonus
        adjustments.append(f"Reflective language bonus: +{bonus:.1f}")

    # Completeness penalty if missing answers
    if completeness < 0.8:
        penalty = (1.0 - completeness) * 10
        score -= penalty
        adjustments.append(f"Incompleteness penalty: -{penalty:.1f} (completeness={completeness:.2f})")

    return round(max(0.0, score), 2), adjustments


def compute_reliability(
    completeness: float,
    dataset_availability: float,
    contradiction_risk: float,
    avg_answer_length: float,
    embedding_available: bool,
) -> Tuple[str, float]:
    """
    Compute reliability label (High/Medium/Low) and score.
    Returns (label, score_0_to_1).
    """
    from app.config import RELIABILITY_HIGH_THRESHOLD, RELIABILITY_MEDIUM_THRESHOLD

    score = (
        completeness * 0.3
        + dataset_availability * 0.2
        + (1.0 - min(1.0, contradiction_risk)) * 0.2
        + min(1.0, avg_answer_length / 50) * 0.2
        + (0.1 if embedding_available else 0.0)
    )
    score = round(min(1.0, score), 3)

    if score >= RELIABILITY_HIGH_THRESHOLD:
        label = "High"
    elif score >= RELIABILITY_MEDIUM_THRESHOLD:
        label = "Medium"
    else:
        label = "Low"

    return label, score
