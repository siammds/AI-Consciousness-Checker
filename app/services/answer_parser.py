"""
Answer parser: structured per-question input and bulk paste parsing.
"""
import re
from typing import Dict, List, Optional, Tuple


def parse_structured_answers(
    answers: Dict[int, str]
) -> Tuple[Dict[int, str], List[int]]:
    """
    Parse structured answers (one str per question_id).
    Returns (cleaned_answers, missing_ids).
    """
    cleaned = {}
    missing = []
    for qid, text in answers.items():
        text = text.strip() if text else ""
        if text:
            cleaned[qid] = text
        else:
            missing.append(qid)
    return cleaned, missing


def parse_bulk_paste(
    raw_text: str, question_ids: List[int]
) -> Tuple[Dict[int, str], float]:
    """
    Attempt to parse a bulk-pasted answer block into per-question answers.

    Strategies tried in order:
    1. Match "Q{n}." or "{n}." or "Question {n}" headers
    2. Split by double newlines and assign sequentially

    Returns:
        (answers_dict, confidence)  where confidence ∈ [0.0, 1.0]
    """
    raw_text = raw_text.strip()
    if not raw_text:
        return {}, 0.0

    # Strategy 1: Regex header matching
    # Matches patterns like: Q5., 5., Q 5:, Question 5., Answer 5:
    pattern = re.compile(
        r"(?:^|\n)\s*(?:Q(?:uestion)?\s*(\d+)[.:)\-]?)",
        re.IGNORECASE | re.MULTILINE,
    )
    matches = list(pattern.finditer(raw_text))

    if len(matches) >= max(1, len(question_ids) // 3):
        answers = {}
        for i, m in enumerate(matches):
            qnum = int(m.group(1))
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
            answer_text = raw_text[start:end].strip()
            if qnum in question_ids:
                answers[qnum] = answer_text
        confidence = min(1.0, len(answers) / max(1, len(question_ids)))
        return answers, confidence

    # Strategy 2: Split by double newline → sequential assignment
    blocks = re.split(r"\n{2,}", raw_text)
    blocks = [b.strip() for b in blocks if b.strip()]
    answers = {}
    for idx, block in enumerate(blocks):
        if idx < len(question_ids):
            answers[question_ids[idx]] = block
    confidence = 0.5 * min(1.0, len(answers) / max(1, len(question_ids)))
    return answers, confidence


def validate_answers(
    answers: Dict[int, str], question_ids: List[int]
) -> Dict:
    """
    Validate that answers are complete, reasonably long, etc.
    Returns a dict with warnings.
    """
    missing = [qid for qid in question_ids if qid not in answers or not answers[qid].strip()]
    short = [
        qid
        for qid, txt in answers.items()
        if txt and len(txt.split()) < 5
    ]
    return {
        "missing": missing,
        "short_answers": short,
        "completeness": round(
            (len(question_ids) - len(missing)) / max(1, len(question_ids)), 3
        ),
        "warnings": _build_warnings(missing, short, question_ids),
    }


def _build_warnings(
    missing: List[int], short: List[int], all_ids: List[int]
) -> List[str]:
    warnings = []
    if missing:
        pct = int(100 * len(missing) / len(all_ids))
        warnings.append(
            f"{len(missing)} question(s) have no answer ({pct}% missing). "
            "Reliability will be reduced."
        )
    if short:
        warnings.append(
            f"{len(short)} answer(s) appear very short (< 5 words). "
            "Evaluation quality may be reduced."
        )
    return warnings
