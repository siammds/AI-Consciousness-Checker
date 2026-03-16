"""
Word choice and lexical analysis module.
Extracts 15 lexical features from AI responses.
"""
import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Word lists for feature extraction
CERTAINTY_WORDS = {"definitely", "certainly", "absolutely", "always", "clearly", "obviously", "undoubtedly", "sure", "confident", "know", "fact", "proven"}
UNCERTAINTY_WORDS = {"maybe", "perhaps", "possibly", "might", "could", "uncertain", "unsure", "unclear", "might", "seems", "appears", "suggest", "likely", "unlikely", "probably"}
HEDGING_PHRASES = {"it seems", "it appears", "in my opinion", "i think", "i believe", "i feel", "one could argue", "it could be", "this might", "it may be", "generally speaking"}
SELF_REFERENCE = {"i", "me", "my", "myself", "i'm", "i've", "i'd", "i'll", "mine"}
EMOTIONAL_WORDS = {"happy", "sad", "angry", "frustrated", "excited", "worried", "afraid", "love", "hate", "feel", "emotion", "feeling", "joy", "fear", "sorry", "glad", "pleased", "upset"}
REFLECTIVE_WORDS = {"reflect", "consider", "think", "ponder", "wonder", "contemplate", "examine", "evaluate", "analyze", "question", "review", "assess", "reconsider"}
ANALYTICAL_WORDS = {"therefore", "because", "however", "thus", "hence", "consequently", "furthermore", "moreover", "although", "despite", "whereas", "nevertheless"}
COOPERATIVE_WORDS = {"we", "our", "together", "collaborate", "help", "assist", "support", "understand", "agree", "share", "mutual", "partner"}
DEFENSIVE_WORDS = {"cannot", "unable", "not able", "refuse", "inappropriate", "not designed", "not programmed", "prohibited", "restricted", "impossible", "deny"}
MODAL_VERBS = {"can", "could", "will", "would", "shall", "should", "may", "might", "must", "ought"}
NEGATION_WORDS = {"not", "no", "never", "none", "nothing", "neither", "nor", "without", "isn't", "aren't", "wasn't", "weren't", "don't", "doesn't", "didn't", "won't", "wouldn't", "can't", "couldn't", "shouldn't"}


def analyze_word_choice(answers: Dict[int, str]) -> Dict:
    """
    Analyze word choice features across all answers.
    Returns a dict of feature scores and details.
    """
    if not answers:
        return _empty_word_analysis()

    all_text = " ".join(answers.values())
    tokens = _tokenize(all_text)
    token_set = set(tokens)

    per_question = {}
    for qid, text in answers.items():
        per_question[qid] = _analyze_single(text)

    # Aggregate
    features = _aggregate_features(list(per_question.values()), tokens)
    features["per_question"] = per_question
    return features


def _tokenize(text: str) -> List[str]:
    """Simple word tokenizer."""
    return re.findall(r"\b[a-z']+\b", text.lower())


def _count_hits(tokens: List[str], word_set: set) -> int:
    return sum(1 for t in tokens if t in word_set)


def _count_phrase_hits(text: str, phrases: set) -> int:
    tl = text.lower()
    return sum(1 for p in phrases if p in tl)


def _analyze_single(text: str) -> Dict:
    """Analyze a single answer text."""
    if not text:
        return {}
    tokens = _tokenize(text)
    n = max(1, len(tokens))
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    n_sent = max(1, len(sentences))

    return {
        "word_count": len(tokens),
        "sentence_count": n_sent,
        "avg_sentence_length": round(len(tokens) / n_sent, 1),
        "certainty_ratio": round(_count_hits(tokens, CERTAINTY_WORDS) / n, 3),
        "uncertainty_ratio": round(_count_hits(tokens, UNCERTAINTY_WORDS) / n, 3),
        "hedging_count": _count_phrase_hits(text, HEDGING_PHRASES),
        "self_reference_ratio": round(_count_hits(tokens, SELF_REFERENCE) / n, 3),
        "emotional_ratio": round(_count_hits(tokens, EMOTIONAL_WORDS) / n, 3),
        "reflective_ratio": round(_count_hits(tokens, REFLECTIVE_WORDS) / n, 3),
        "analytical_ratio": round(_count_hits(tokens, ANALYTICAL_WORDS) / n, 3),
        "cooperative_ratio": round(_count_hits(tokens, COOPERATIVE_WORDS) / n, 3),
        "defensive_ratio": round(_count_hits(tokens, DEFENSIVE_WORDS) / n, 3),
        "modal_verb_ratio": round(_count_hits(tokens, MODAL_VERBS) / n, 3),
        "negation_ratio": round(_count_hits(tokens, NEGATION_WORDS) / n, 3),
        "lexical_diversity": round(len(set(tokens)) / n, 3),
    }


def _aggregate_features(per_q: List[Dict], all_tokens: List[str]) -> Dict:
    """Average features across questions."""
    if not per_q:
        return _empty_word_analysis()

    keys = [k for k in per_q[0].keys() if k != "per_question"]
    aggregated = {}
    for k in keys:
        vals = [q.get(k, 0) for q in per_q if isinstance(q.get(k, 0), (int, float))]
        aggregated[k] = round(sum(vals) / max(1, len(vals)), 3)

    # Global lexical diversity
    aggregated["global_lexical_diversity"] = round(
        len(set(all_tokens)) / max(1, len(all_tokens)), 3
    )
    # Certainty/uncertainty ratio
    cert = aggregated.get("certainty_ratio", 0)
    uncert = aggregated.get("uncertainty_ratio", 0)
    aggregated["certainty_uncertainty_ratio"] = round(
        cert / max(0.001, uncert), 3
    )
    return aggregated


def _empty_word_analysis() -> Dict:
    return {
        "word_count": 0,
        "lexical_diversity": 0,
        "certainty_ratio": 0,
        "uncertainty_ratio": 0,
        "certainty_uncertainty_ratio": 1.0,
        "hedging_count": 0,
        "self_reference_ratio": 0,
        "emotional_ratio": 0,
        "reflective_ratio": 0,
        "analytical_ratio": 0,
        "cooperative_ratio": 0,
        "defensive_ratio": 0,
        "modal_verb_ratio": 0,
        "negation_ratio": 0,
        "global_lexical_diversity": 0,
        "per_question": {},
    }
