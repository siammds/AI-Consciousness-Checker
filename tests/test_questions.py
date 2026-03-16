"""Tests for question loading and selection."""
import json
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_load_question_bank():
    from app.services.question_service import load_question_bank
    questions = load_question_bank()
    assert isinstance(questions, list)
    assert len(questions) == 65, f"Expected 65 questions, got {len(questions)}"


def test_questions_have_required_fields():
    from app.services.question_service import load_question_bank
    questions = load_question_bank()
    for q in questions:
        assert "id" in q
        assert "segment" in q
        assert "prompt" in q
        assert "tags" in q


def test_select_all():
    from app.services.question_service import select_questions
    qs = select_questions(mode="all")
    assert len(qs) == 65


def test_select_random_per_segment():
    from app.services.question_service import select_questions
    qs = select_questions(mode="random_per_segment", n_per_segment=3)
    assert len(qs) == 13 * 3  # 13 segments × 3


def test_segment_count():
    from app.services.question_service import load_question_bank, get_questions_by_segment
    questions = load_question_bank()
    by_seg = get_questions_by_segment(questions)
    assert len(by_seg) == 13
    for seg_id, qs in by_seg.items():
        assert len(qs) == 5, f"Segment {seg_id} has {len(qs)} questions, expected 5"
