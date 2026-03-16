"""
Dataset loader: load human-reference datasets from HuggingFace.
Gracefully handles unavailability and reports status/warnings.
"""
import logging
from typing import Dict, List, Optional, Tuple
from app.config import DATASETS

logger = logging.getLogger(__name__)

# Cache loaded datasets in memory
_dataset_cache: Dict[str, Optional[object]] = {}
_dataset_status: Dict[str, str] = {}


def load_all_datasets() -> Dict[str, Optional[object]]:
    """
    Attempt to load all 5 reference datasets.
    Returns dict of {name: dataset_or_None}.
    """
    for name, hf_path in DATASETS.items():
        if name not in _dataset_cache:
            _try_load_dataset(name, hf_path)
    return _dataset_cache


def _try_load_dataset(name: str, hf_path: str):
    """Attempt to load a single dataset; cache None on failure."""
    try:
        from datasets import load_dataset
        logger.info(f"Loading dataset: {name} from {hf_path}")
        splits = {"multinli": "validation_matched", "sst2": "validation"}
        split = splits.get(name, "train")
        ds = load_dataset(hf_path, split=split, trust_remote_code=True)
        _dataset_cache[name] = ds
        _dataset_status[name] = "loaded"
        logger.info(f"Dataset {name} loaded: {len(ds)} rows")
    except Exception as e:
        logger.warning(f"Could not load dataset {name}: {e}")
        _dataset_cache[name] = None
        _dataset_status[name] = f"unavailable: {str(e)[:80]}"


def get_dataset_status() -> Dict[str, str]:
    """Return status of all datasets."""
    # Ensure all have been attempted
    for name, hf_path in DATASETS.items():
        if name not in _dataset_status:
            _try_load_dataset(name, hf_path)
    return _dataset_status


def get_reference_texts(name: str, n: int = 200) -> List[str]:
    """
    Extract up to n text samples from a loaded dataset.
    Returns empty list if dataset is unavailable.
    """
    ds = _dataset_cache.get(name)
    if ds is None:
        return []
    try:
        texts = []
        text_fields = ["text", "sentence", "utterance", "premise", "response"]
        for row in ds.select(range(min(n, len(ds)))):
            for field in text_fields:
                if field in row and row[field]:
                    texts.append(str(row[field])[:512])
                    break
        return texts
    except Exception as e:
        logger.warning(f"Could not extract texts from {name}: {e}")
        return []


def get_availability_factor() -> float:
    """
    Returns a factor in [0.0, 1.0] representing how many datasets are loaded.
    Used in reliability calculation.
    """
    status = get_dataset_status()
    loaded = sum(1 for s in status.values() if s == "loaded")
    return loaded / max(1, len(DATASETS))


def get_dataset_warnings() -> List[str]:
    """Return human-readable warnings for unavailable datasets."""
    status = get_dataset_status()
    warnings = []
    for name, st in status.items():
        if st != "loaded":
            warnings.append(
                f"Dataset '{name}' unavailable — evaluation confidence reduced. ({st})"
            )
    return warnings
