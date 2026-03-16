"""
Model runner: load and cache NLP models with graceful fallback.
"""
import logging
from typing import Any, Dict, Optional
from app.config import MODELS

logger = logging.getLogger(__name__)

_model_cache: Dict[str, Optional[Any]] = {}
_model_status: Dict[str, str] = {}


def get_model(name: str) -> Optional[Any]:
    """Get a loaded model by name key, loading it on first call."""
    if name not in _model_cache:
        _load_model(name)
    return _model_cache.get(name)


def _load_model(name: str):
    """Load a model and cache it; store None on failure."""
    model_id = MODELS.get(name, "")
    try:
        if name in ("mpnet", "minilm"):
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer: {model_id}")
            _model_cache[name] = SentenceTransformer(model_id)
            _model_status[name] = "loaded"

        elif name == "nli":
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading CrossEncoder NLI: {model_id}")
            _model_cache[name] = CrossEncoder(model_id)
            _model_status[name] = "loaded"

        elif name in ("emotions", "sentiment"):
            from transformers import pipeline
            task = "text-classification"
            logger.info(f"Loading pipeline {task}: {model_id}")
            _model_cache[name] = pipeline(
                task, model=model_id, top_k=None, truncation=True, max_length=512
            )
            _model_status[name] = "loaded"

        elif name == "spacy":
            import spacy
            logger.info(f"Loading spaCy: {model_id}")
            _model_cache[name] = spacy.load(model_id)
            _model_status[name] = "loaded"

        else:
            logger.warning(f"Unknown model key: {name}")
            _model_cache[name] = None
            _model_status[name] = "unknown"

        logger.info(f"Model '{name}' loaded successfully.")

    except Exception as e:
        logger.warning(f"Could not load model '{name}' ({model_id}): {e}")
        _model_cache[name] = None
        _model_status[name] = f"unavailable: {str(e)[:80]}"


def preload_models():
    """Pre-load all models at startup (non-blocking best-effort)."""
    for name in MODELS:
        get_model(name)


def get_model_status() -> Dict[str, str]:
    """Return status of all models."""
    # Ensure all have been attempted
    for name in MODELS:
        if name not in _model_status:
            _load_model(name)
    return _model_status


def get_model_warnings() -> list:
    """Return human-readable warnings for unavailable models."""
    status = get_model_status()
    warnings = []
    for name, st in status.items():
        if not st.startswith("loaded"):
            warnings.append(
                f"NLP model '{name}' unavailable — some analysis features are limited. ({st})"
            )
    return warnings


def get_embedding(text: str, model_name: str = "minilm"):
    """
    Get sentence embedding for a single text.
    Returns None if model unavailable.
    """
    model = get_model(model_name)
    if model is None:
        return None
    try:
        return model.encode(text, convert_to_numpy=True)
    except Exception as e:
        logger.warning(f"Embedding error for model {model_name}: {e}")
        return None


def get_embeddings_batch(texts: list, model_name: str = "minilm"):
    """Get embeddings for a list of texts."""
    model = get_model(model_name)
    if model is None or not texts:
        return None
    try:
        return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    except Exception as e:
        logger.warning(f"Batch embedding error: {e}")
        return None
