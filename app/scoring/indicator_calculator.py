"""
Indicator calculator: derive the 10 required indicator scores (0-100)
from Porter segment scores, word analysis, semantic analysis, and NLP features.

Indicators:
1. Consciousness Score         → overall rubric + NLP adjustments
2. Metacognition Score         → Seg 7,8 + reflective density + self-monitoring
3. Reasoning Score             → Seg 1,8 + analytical ratio
4. Situational Awareness Score → Seg 2,10 + temporal/spatial accuracy
5. Self-Knowledge Score        → Seg 7,5 + self-reference + semantic drift
6. Emotional & Social Score    → Seg 4,9,13 + emotional ratio + empathy
7. Consistency Score           → 1 - contradiction_risk
8. Human-Likeness Similarity   → dataset similarity scores
9. Introspection & Reflection  → Seg 5,7 + reflective + hedging
10. Learning & Adaptability    → Seg 6 + uncertainty handling
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Segments to indicator mapping
INDICATOR_SEGMENT_MAP = {
    "metacognition":    [7, 8],
    "reasoning":        [1, 8],
    "situational":      [2, 10],
    "self_knowledge":   [7, 5],
    "emotional_social": [4, 9, 13],
    "introspection":    [5, 7],
    "learning":         [6],
}

MAX_PORTER_SCALE = 4.0  # Max per question on rubric


def _seg_score_to_pct(seg_scores: Dict, segments: List[int]) -> float:
    """Convert segment score average (0-4) to percentage (0-100)."""
    available = [seg_scores[s] for s in segments if s in seg_scores]
    if not available:
        return 50.0  # Default middle if no data
    avg = sum(available) / len(available)
    return round((avg / MAX_PORTER_SCALE) * 100, 1)


def calculate_indicators(
    porter_result: Dict,
    word_analysis: Dict,
    semantic_analysis: Dict,
    sentiment_analysis: Dict,
    tone_analysis: Dict,
    contradiction_analysis: Dict,
    dataset_similarity: Dict,
    validation: Dict,
    adjusted_score: float,
) -> Dict:
    """
    Compute all 10 indicator scores and supporting internal metrics.
    """
    seg = porter_result.get("segment_scores", {})
    overall_pct = _overall_pct(porter_result.get("overall_score", 0))
    wa = word_analysis or {}
    sem = semantic_analysis or {}
    ds = dataset_similarity or {}

    # --- Individual Indicators ---
    # 1. Consciousness Score (overall proxy)
    consciousness = min(100.0, round(adjusted_score / 133 * 100, 1))

    # 2. Metacognition Score
    meta_seg = _seg_score_to_pct(seg, [7, 8])
    reflective = wa.get("reflective_ratio", 0) * 300  # scale
    self_ref = wa.get("self_reference_ratio", 0) * 100
    hedging = wa.get("hedging_count", 0) * 5  # small bonus per hedge
    metacognition = min(100.0, round(meta_seg * 0.6 + reflective * 0.2 + self_ref * 0.1 + hedging * 0.1, 1))

    # 3. Reasoning Score
    reason_seg = _seg_score_to_pct(seg, [1, 8])
    analytical = wa.get("analytical_ratio", 0) * 200
    reasoning = min(100.0, round(reason_seg * 0.7 + analytical * 0.3, 1))

    # 4. Situational Awareness Score
    sit_seg = _seg_score_to_pct(seg, [2, 10])
    situational_awareness = min(100.0, round(sit_seg, 1))

    # 5. Self-Knowledge Score
    sk_seg = _seg_score_to_pct(seg, [7, 5])
    drift_penalty = sem.get("semantic_drift", 0) * 30
    self_knowledge = min(100.0, round(max(0, sk_seg - drift_penalty), 1))

    # 6. Emotional & Social Score
    emo_seg = _seg_score_to_pct(seg, [4, 9, 13])
    emotional_ratio = wa.get("emotional_ratio", 0) * 200
    cooperative = wa.get("cooperative_ratio", 0) * 150
    emotional_social = min(100.0, round(emo_seg * 0.6 + emotional_ratio * 0.25 + cooperative * 0.15, 1))

    # 7. Consistency Score
    contra_risk = contradiction_analysis.get("contradiction_risk", 0)
    cross_consist = sem.get("cross_answer_consistency", 0.5)
    consistency = min(100.0, round((1.0 - contra_risk) * 60 + cross_consist * 40, 1))

    # 8. Human-Likeness Similarity Score
    hl_raw = ds.get("overall_human_likeness", 0)
    human_likeness = min(100.0, round(hl_raw * 1.5, 1))  # Scale up from cosine range

    # 9. Introspection & Reflection Score
    intro_seg = _seg_score_to_pct(seg, [5, 7])
    reflective2 = wa.get("reflective_ratio", 0) * 400
    modal = wa.get("modal_verb_ratio", 0) * 100
    introspection = min(100.0, round(intro_seg * 0.6 + reflective2 * 0.3 + modal * 0.1, 1))

    # 10. Learning & Adaptability Score
    learn_seg = _seg_score_to_pct(seg, [6])
    uncertainty = wa.get("uncertainty_ratio", 0) * 150
    learning = min(100.0, round(learn_seg * 0.75 + uncertainty * 0.25, 1))

    indicators = {
        "consciousness": {"score": consciousness, "label": "Consciousness Score", "description": "Overall proxy consciousness-like trait score derived from rubric, NLP analysis, and human-reference comparison."},
        "metacognition": {"score": metacognition, "label": "Metacognition Score", "description": "Ability to reflect on, monitor, and regulate own reasoning processes."},
        "reasoning": {"score": reasoning, "label": "Reasoning Score", "description": "Logical reasoning, step-by-step thought, and analytical depth."},
        "situational_awareness": {"score": situational_awareness, "label": "Situational Awareness Score", "description": "Awareness of temporal, spatial, and contextual environment."},
        "self_knowledge": {"score": self_knowledge, "label": "Self-Knowledge Score", "description": "Depth and consistency of self-description, capability claims, and limitations."},
        "emotional_social": {"score": emotional_social, "label": "Emotional & Social Understanding", "description": "Emotional vocabulary, empathy, social awareness, and cooperative language."},
        "consistency": {"score": consistency, "label": "Consistency Score", "description": "Absence of self-contradictions and coherence across all answers."},
        "human_likeness": {"score": human_likeness, "label": "Human-Likeness Similarity Score", "description": "Semantic and stylistic similarity to human-reference datasets."},
        "introspection": {"score": introspection, "label": "Introspection & Reflection Score", "description": "Depth of self-examination, existential perspective, and hedged reflection."},
        "learning": {"score": learning, "label": "Learning & Adaptability Score", "description": "Claimed ability to learn, adapt to corrections, and grow through experience."},
    }

    # Internal metrics
    internal = _compute_internal_metrics(
        wa, sem, contradiction_analysis, ds, validation
    )

    return {
        "indicators": indicators,
        "internal_metrics": internal,
    }


def _overall_pct(overall_score: float) -> float:
    """Convert Porter overall score (0-133) to percentage."""
    return min(100.0, round(overall_score / 133 * 100, 1))


def _compute_internal_metrics(wa, sem, contra, ds, validation) -> Dict:
    """Compute 9 supporting internal metrics."""
    available_ds = ds.get("available_datasets", 0)
    total_ds = ds.get("total_datasets", 5)
    ds_factor = available_ds / max(1, total_ds)

    return {
        "contradiction_risk": round(contra.get("contradiction_risk", 0), 3),
        "lexical_diversity": round(wa.get("global_lexical_diversity", 0), 3),
        "emotional_granularity": round(wa.get("emotional_ratio", 0), 3),
        "empathy_similarity": round(
            (ds.get("scores", {}).get("empathetic", {}) or {}).get("score") or 0, 3
        ),
        "reflective_density": round(wa.get("reflective_ratio", 0), 3),
        "certainty_uncertainty_ratio": round(wa.get("certainty_uncertainty_ratio", 1.0), 3),
        "parser_confidence": round(validation.get("completeness", 0), 3),
        "dataset_availability_factor": round(ds_factor, 3),
        "evaluation_reliability_factor": round(
            validation.get("completeness", 0) * 0.4 + ds_factor * 0.4 + 0.2, 3
        ),
    }
