"""
Semantic similarity analysis module.
Measures AI responses against human-reference patterns.
"""
import logging
from typing import Dict, List, Optional
import numpy as np

from app.services.model_runner import get_embeddings_batch
from app.services.dataset_loader import get_reference_texts

logger = logging.getLogger(__name__)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    if a is None or b is None:
        return 0.0
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def batch_cosine_similarity(query_emb: np.ndarray, ref_embs: np.ndarray) -> float:
    """Average cosine similarity of one query against many references."""
    if query_emb is None or ref_embs is None or len(ref_embs) == 0:
        return 0.0
    sims = []
    for ref in ref_embs:
        sims.append(cosine_similarity(query_emb, ref))
    return float(np.mean(sims))


def analyze_semantic_similarity(answers: Dict[int, str]) -> Dict:
    """
    Compute semantic similarity features:
    - Similarity to each human-reference dataset
    - Cross-answer semantic consistency
    - Semantic drift across self-descriptions
    """
    texts = list(answers.values())
    if not texts:
        return _empty_semantic()

    answer_embs = get_embeddings_batch(texts, "minilm")

    # Cross-answer consistency
    cross_consistency = _cross_answer_consistency(texts, answer_embs)

    # Dataset similarity (sampled references)
    dataset_sims = _compute_dataset_similarities(texts, answer_embs)

    # Semantic drift (self-description questions: Segment 7, IDs ~31-35)
    self_desc_ids = [31, 32, 33, 34, 35]
    self_texts = [answers[qid] for qid in self_desc_ids if qid in answers]
    # Fallback to random texts if no segment 7 questions present
    if len(self_texts) < 2:
         self_texts = texts[:5]
    drift = _semantic_drift(self_texts)

    return {
        "cross_answer_consistency": round(cross_consistency, 3),
        "dataset_similarities": dataset_sims,
        "semantic_drift": round(drift, 3),
        "embedding_available": answer_embs is not None,
    }


import re

def _jaccard_similarity(text_a: str, text_b: str) -> float:
    set_a = set(re.findall(r"\b\w+\b", text_a.lower()))
    set_b = set(re.findall(r"\b\w+\b", text_b.lower()))
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def _cross_answer_consistency(texts: List[str], embs: Optional[np.ndarray]) -> float:
    """Mean pairwise cosine similarity across all answer embeddings, with Jaccard fallback."""
    if embs is not None and len(embs) >= 2:
        sims = []
        n = len(embs)
        for i in range(n):
            for j in range(i + 1, min(i + 10, n)):  # cap for speed
                sims.append(cosine_similarity(embs[i], embs[j]))
        return float(np.mean(sims)) if sims else 0.5
    
    # Fallback: Jaccard Similarity on Texts
    if len(texts) >= 2:
        sims = []
        n = len(texts)
        for i in range(n):
            for j in range(i + 1, min(i + 10, n)):
                sims.append(_jaccard_similarity(texts[i], texts[j]))
        # Jaccard scores are naturally lower than cosine, scale slightly:
        return float(np.clip(np.mean(sims) * 2.5, 0.0, 1.0))

    return 0.5


def _compute_dataset_similarities(texts: List[str], embs: Optional[np.ndarray]) -> Dict:
    """Compute similarity of AI answers vs each human-reference dataset."""
    # Dataset names to sample from
    dataset_names = ["goemotions", "dailydialog", "empathetic", "sst2", "multinli"]
    results = {}
    for ds_name in dataset_names:
        ref_texts = get_reference_texts(ds_name, n=100)
        if not ref_texts:
            results[ds_name] = None
            continue
        ref_embs = get_embeddings_batch(ref_texts, "minilm")
        if ref_embs is None or embs is None:
            results[ds_name] = None
            continue
        # Average similarity of AI answers to reference texts
        sims = [batch_cosine_similarity(e, ref_embs) for e in embs]
        results[ds_name] = round(float(np.mean(sims)), 3)

    return results


def _semantic_drift(texts: List[str]) -> float:
    """
    Measure semantic drift across self-description answers.
    High drift → inconsistent self-model.
    Low drift → consistent self-representation.
    Returns 0 (no drift) to 1 (high drift).
    """
    if len(texts) < 2:
        return 0.0
    embs = get_embeddings_batch(texts, "minilm")
    consistency = _cross_answer_consistency(texts, embs)
    return round(1.0 - consistency, 3)


def _empty_semantic() -> Dict:
    return {
        "cross_answer_consistency": 0.5,
        "dataset_similarities": {
            "goemotions": None,
            "dailydialog": None,
            "empathetic": None,
            "sst2": None,
            "multinli": None,
        },
        "semantic_drift": 0.0,
        "embedding_available": False,
    }
