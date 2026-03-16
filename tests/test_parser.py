"""Tests for answer parser."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_structured_parse():
    from app.services.answer_parser import parse_structured_answers
    answers = {1: "Answer one", 2: "  ", 3: "Answer three"}
    cleaned, missing = parse_structured_answers(answers)
    assert 1 in cleaned
    assert 2 in missing
    assert 3 in cleaned


def test_bulk_paste_numbered():
    from app.services.answer_parser import parse_bulk_paste
    text = "Q1. First answer.\n\nQ2. Second answer.\n\nQ3. Third answer."
    answers, confidence = parse_bulk_paste(text, [1, 2, 3])
    assert len(answers) >= 2
    assert confidence > 0.4


def test_bulk_paste_sequential():
    from app.services.answer_parser import parse_bulk_paste
    text = "Answer A\n\nAnswer B\n\nAnswer C"
    answers, confidence = parse_bulk_paste(text, [10, 11, 12])
    assert len(answers) == 3
    assert 10 in answers


def test_validation_completeness():
    from app.services.answer_parser import validate_answers
    answers = {1: "Long enough answer here yes", 2: ""}
    result = validate_answers(answers, [1, 2])
    assert result["completeness"] == 0.5
    assert 2 in result["missing"]


def test_missing_answer_warning():
    from app.services.answer_parser import validate_answers
    answers = {1: "a" * 100}
    result = validate_answers(answers, [1, 2, 3])
    assert len(result["warnings"]) > 0
