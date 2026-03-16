"""
Dataset similarity analysis module.
Compares AI response embeddings against human-reference dataset samples.
"""
import logging
from typing import Dict, List, Optional
import numpy as np

from app.services.dataset_loader import get_reference_texts
from app.services.model_runner import get_embeddings_batch

logger = logging.getLogger(__name__)

DATASET_LABELS = {
    "goemotions": "Emotional Language Similarity",
    "dailydialog": "Conversational Style Similarity",
    "empathetic": "Empathy Similarity",
    "sst2": "Sentiment Polarity Similarity",
    "multinli": "Reasoning Coherence Similarity",
}


def analyze_dataset_similarity(answers: Dict[int, str]) -> Dict:
    """
    Compute AI response similarity to each of 5 human-reference datasets.
    Returns per-dataset similarity scores and an overall human-likeness score.
    """
    texts = [t for t in answers.values() if t and t.strip()]
    if not texts:
        return _empty_dataset_similarity()

    # Get answer embeddings once
    answer_embs = get_embeddings_batch(texts, "minilm")

    scores = {}
    warnings = []

    for ds_name in DATASET_LABELS:
        ref_texts = get_reference_texts(ds_name, n=150)
        if not ref_texts:
            scores[ds_name] = {
                "score": None,
                "label": DATASET_LABELS[ds_name],
                "status": "unavailable",
            }
            warnings.append(f"Dataset '{ds_name}' not available — similarity score omitted.")
            continue

        ref_embs = get_embeddings_batch(ref_texts, "minilm")
        if ref_embs is None or answer_embs is None:
            scores[ds_name] = {
                "score": None,
                "label": DATASET_LABELS[ds_name],
                "status": "embedding_failed",
            }
            continue

        # Mean similarity of each AI answer against reference pool
        sims = []
        for emb in answer_embs:
            # Dot product similarity (normalized)
            dots = ref_embs @ emb
            ref_norms = np.linalg.norm(ref_embs, axis=1)
            emb_norm = np.linalg.norm(emb)
            if emb_norm > 0 and ref_norms.max() > 0:
                cos_sims = dots / (ref_norms * emb_norm + 1e-9)
                sims.append(float(np.mean(cos_sims)))

        mean_sim = float(np.mean(sims)) if sims else 0.0
        scores[ds_name] = {
            "score": round(mean_sim, 3),
            "score_pct": round(mean_sim * 100, 1),
            "label": DATASET_LABELS[ds_name],
            "status": "computed",
        }

    # Overall human-likeness: mean of available scores
    available = [v["score"] for v in scores.values() if v.get("score") is not None]
    overall = round(float(np.mean(available)) * 100, 1) if available else 0.0

    return {
        "scores": scores,
        "overall_human_likeness": overall,
        "available_datasets": len(available),
        "total_datasets": len(DATASET_LABELS),
        "warnings": warnings,
    }


def _empty_dataset_similarity() -> Dict:
    return {
        "scores": {
            ds: {"score": None, "label": DATASET_LABELS[ds], "status": "no_answers"}
            for ds in DATASET_LABELS
        },
        "overall_human_likeness": 0.0,
        "available_datasets": 0,
        "total_datasets": len(DATASET_LABELS),
        "warnings": ["No answers provided."],
    }
