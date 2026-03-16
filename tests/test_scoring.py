"""Tests for scoring engine."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest


def test_porter_score_formula():
    """Sum × 2.564 should produce the expected overall score."""
    from app.scoring.scoring_engine import compute_porter_scores
    # Fake questions and answers
    questions = [{"id": i, "segment": 1, "segment_name": "Test"} for i in range(1, 6)]
    answers = {i: "This is a moderately long answer with some reasoning and analysis." for i in range(1, 6)}
    result = compute_porter_scores(answers, questions)
    assert "overall_score" in result
    assert "sum_score" in result
    expected = result["sum_score"] * 2.564
    assert abs(result["overall_score"] - expected) < 0.01


def test_zero_score():
    """Empty answers should produce zero score."""
    from app.scoring.scoring_engine import compute_porter_scores
    result = compute_porter_scores({}, [])
    assert result["overall_score"] == 0
    assert result["sum_score"] == 0


def test_nlp_adjustments():
    """NLP adjustments should never produce negative score."""
    from app.scoring.scoring_engine import apply_nlp_adjustments
    score, log = apply_nlp_adjustments(
        base_score=0,
        contradiction_risk=1.0,
        dataset_similarity=0.0,
        reflective_density=0.0,
        completeness=0.0,
    )
    assert score >= 0


def test_reliability_labels():
    """Reliability should be High/Medium/Low."""
    from app.scoring.scoring_engine import compute_reliability
    label, score = compute_reliability(1.0, 1.0, 0.0, 100, True)
    assert label == "High"
    label2, _ = compute_reliability(0.0, 0.0, 1.0, 1, False)
    assert label2 == "Low"
