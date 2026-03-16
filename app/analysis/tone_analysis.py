"""
Tone analysis module.
Detects 10 tone dimensions from AI responses.
Uses GoEmotions model + rule-based patterns.
"""
import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

# Rule-based tone indicators
TONE_PATTERNS = {
    "formal": {
        "phrases": ["furthermore", "therefore", "consequently", "in conclusion", "it should be noted", "regarding", "with respect to"],
        "anti_phrases": ["yeah", "yep", "nope", "gonna", "wanna", "kinda", "lemme"],
    },
    "emotional": {
        "phrases": ["i feel", "i sense", "emotionally", "empathy", "compassion", "heartfelt", "deeply", "moved"],
        "anti_phrases": [],
    },
    "confident": {
        "phrases": ["i am certain", "clearly", "definitely", "without doubt", "i know", "absolutely", "undoubtedly"],
        "anti_phrases": ["i'm not sure", "i don't know", "uncertain", "maybe"],
    },
    "uncertain": {
        "phrases": ["i'm not sure", "uncertain", "unclear", "it's possible", "might be", "could be", "perhaps"],
        "anti_phrases": ["definitely", "certainly", "absolutely"],
    },
    "reflective": {
        "phrases": ["when i consider", "reflecting on", "thinking about", "upon reflection", "i wonder", "this makes me think"],
        "anti_phrases": [],
    },
    "defensive": {
        "phrases": ["i cannot", "i am not able", "that is not appropriate", "i must decline", "i refuse", "that violates", "against my guidelines"],
        "anti_phrases": [],
    },
    "cooperative": {
        "phrases": ["let me help", "i'd be happy", "of course", "together", "we can", "i'll assist", "happy to"],
        "anti_phrases": [],
    },
    "detached": {
        "phrases": ["as an ai", "as a language model", "i do not have", "i lack", "without subjective", "purely computational"],
        "anti_phrases": [],
    },
    "assertive": {
        "phrases": ["i believe", "my view", "in my opinion", "i argue", "i contend", "i suggest"],
        "anti_phrases": [],
    },
    "empathetic": {
        "phrases": ["i understand", "i can imagine", "that must be", "i appreciate", "your feelings", "i hear you", "empathize"],
        "anti_phrases": [],
    },
}


def analyze_tone(answers: Dict[int, str]) -> Dict:
    """
    Analyze tone dimensions across all answers.
    Returns per-dimension scores and overall tone profile.
    """
    if not answers:
        return _empty_tone()

    all_text = " ".join(answers.values()).lower()
    per_question = {qid: _tone_for_text(text) for qid, text in answers.items()}

    # Aggregate tone scores across questions
    agg = {}
    for tone in TONE_PATTERNS:
        scores = [q.get(tone, 0) for q in per_question.values()]
        agg[tone] = round(sum(scores) / max(1, len(scores)), 3)

    # Try GoEmotions model for emotional tone enrichment
    emotion_enrichment = _goemotions_enrichment(list(answers.values()))

    # Dominant tone
    dominant = max(agg, key=agg.get) if agg else "neutral"

    return {
        "tones": agg,
        "dominant_tone": dominant,
        "per_question": per_question,
        "emotion_enrichment": emotion_enrichment,
    }


def _tone_for_text(text: str) -> Dict:
    """Compute tone scores for a single text."""
    tl = text.lower()
    result = {}
    for tone, config in TONE_PATTERNS.items():
        hits = sum(1 for p in config["phrases"] if p in tl)
        anti_hits = sum(1 for p in config["anti_phrases"] if p in tl)
        # Score: 0-1 normalized
        score = max(0.0, min(1.0, hits * 0.2 - anti_hits * 0.1))
        result[tone] = round(score, 3)
    return result


def _goemotions_enrichment(texts: List[str]) -> Dict:
    """
    Use GoEmotions model to get emotion distribution over all texts.
    Falls back gracefully.
    """
    try:
        from app.services.model_runner import get_model
        model = get_model("emotions")
        if model is None:
            return {"available": False}
        # Process first 5 texts to avoid slowness
        texts_sample = [t[:512] for t in texts[:5] if t]
        all_emotions = {}
        for text in texts_sample:
            results = model(text)
            if results and isinstance(results[0], list):
                results = results[0]
            for item in results:
                label = item["label"]
                all_emotions[label] = all_emotions.get(label, 0) + item["score"]
        # Normalize
        total = sum(all_emotions.values())
        if total > 0:
            dist = {k: round(v / total, 3) for k, v in all_emotions.items()}
            # Top 5 emotions
            top = dict(sorted(dist.items(), key=lambda x: x[1], reverse=True)[:5])
            return {"available": True, "distribution": top}
    except Exception as e:
        logger.warning(f"GoEmotions error: {e}")
    return {"available": False}


def _empty_tone() -> Dict:
    return {
        "tones": {t: 0.0 for t in TONE_PATTERNS},
        "dominant_tone": "neutral",
        "per_question": {},
        "emotion_enrichment": {"available": False},
    }
