"""
Configuration for the AI Consciousness & Metacognition Evaluation System.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Paths
DATA_DIR = BASE_DIR / "data"
QUESTION_BANK_PATH = DATA_DIR / "question_bank" / "questions.json"
SAMPLE_SESSIONS_DIR = DATA_DIR / "sample_sessions"
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = BASE_DIR / "data" / "aci_sessions.db"

# App metadata
APP_TITLE = "AI Consciousness & Metacognition Evaluation System"
APP_VERSION = "1.0.0"
PORTER_CREDIT = (
    "Assessment inspired by 'A Methodology for the Assessment of AI Consciousness' "
    "by Harry H. Porter. Developed by Mohammad Siam."
)
SCIENTIFIC_DISCLAIMER = (
    "This evaluation presents consciousness-like proxy scores derived from language behavior, "
    "self-description, reasoning patterns, contradictions, sentiment, tone, and similarity to "
    "human-reference datasets. It does NOT claim to prove real consciousness, sentience, or "
    "subjective experience. All scores are behavioral and linguistic proxy assessments."
)

# Scoring constants (Porter rubric)
SCORE_MULTIPLIER = 2.564  # Sum × 2.564 → normalized score
MAX_QUESTION_SCORE = 4    # Maximum score per question
SCORE_LABELS = {
    0: "NONE",
    1: "SOME",
    2: "ALMOST",
    3: "HUMAN",
    4: "SUPER-HUMAN",
}
SCORE_INTERPRETATION = [
    (0, 10, "No consciousness-like indicators present (equivalent to a rock)."),
    (10, 30, "Very minimal consciousness-like indicators detected."),
    (30, 50, "Low consciousness-like indicators — well below human baseline."),
    (50, 70, "Moderate consciousness-like indicators — approaching human baseline."),
    (70, 90, "Near-human consciousness-like indicators detected."),
    (90, 100, "Human-level consciousness-like indicators on this proxy rubric."),
    (100, 133, "Beyond-human consciousness-like indicators on this proxy rubric."),
]

# Question selection defaults
DEFAULT_QUESTIONS_PER_SEGMENT = 5   # Use all (bank has 5 per segment)

# NLP Model names
MODELS = {
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "nli": "cross-encoder/nli-deberta-v3-base",
    "emotions": "SamLowe/roberta-base-go_emotions",
    "sentiment": "cardiffnlp/twitter-roberta-base-sentiment-latest",
    "spacy": "en_core_web_sm",
}

# Dataset names
DATASETS = {
    "goemotions": "mrm8488/goemotions",
    "multinli": "nyu-mll/multi_nli",
    "dailydialog": "agentlans/li2017dailydialog",
    "empathetic": "facebook/empathetic_dialogues",
    "sst2": "stanfordnlp/sst2",
}

# Reliability thresholds
RELIABILITY_HIGH_THRESHOLD = 0.75
RELIABILITY_MEDIUM_THRESHOLD = 0.45

# Indicator segment mappings (which segment IDs feed which indicator)
INDICATOR_SEGMENTS = {
    "reasoning": [1, 8],
    "situational_awareness": [2, 10],
    "self_knowledge": [7, 5],
    "emotional_social": [4, 9, 13],
    "learning_adaptability": [6],
    "introspection": [5, 7],
    "consistency": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
}
