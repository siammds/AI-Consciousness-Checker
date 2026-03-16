"""Question service: load, filter, and select questions from the bank."""
import json
import random
from pathlib import Path
from typing import Dict, List, Optional
from app.config import QUESTION_BANK_PATH, DEFAULT_QUESTIONS_PER_SEGMENT


def load_question_bank() -> List[Dict]:
    """Load all questions from the JSON bank."""
    with open(QUESTION_BANK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["questions"]


def get_questions_by_segment(questions: List[Dict]) -> Dict[int, List[Dict]]:
    """Group questions by segment number."""
    segments: Dict[int, List[Dict]] = {}
    for q in questions:
        seg = q["segment"]
        segments.setdefault(seg, []).append(q)
    return segments


def select_questions(
    mode: str = "ten_mixed",
    n_per_segment: Optional[int] = None,
    total_n: Optional[int] = None,
    segment_ids: Optional[List[int]] = None,
) -> List[Dict]:
    """
    Select questions from the bank.

    Args:
        mode: 'thirteen_mixed' (default) | 'all' | 'random_per_segment' | 'random_total'
              'thirteen_mixed' = 1 question from each of 13 randomly chosen segments
        n_per_segment: Number per segment (used in 'random_per_segment' mode)
        total_n: Total random questions (used in 'random_total' mode)
        segment_ids: Filter to these segments only (None = all)

    Returns:
        List of selected question dicts (in thirteen_mixed mode, renumbered 1-13).
    """
    all_questions = load_question_bank()

    # Filter by segment if requested
    if segment_ids:
        all_questions = [q for q in all_questions if q["segment"] in segment_ids]

    by_segment = get_questions_by_segment(all_questions)

    if mode in ["ten_mixed", "thirteen_mixed"]:
        # Pick 13 random segments (or fewer if bank has <13), then 1 Q per segment
        available_segs = list(by_segment.keys())
        chosen_segs = random.sample(available_segs, min(13, len(available_segs)))
        selected = []
        for seg_id in chosen_segs:
            q = random.choice(by_segment[seg_id])
            selected.append(q)
        # Renumber 1-13 so front-end shows Q1…Q13 with no segment labels
        result = []
        for i, q in enumerate(selected, 1):
            q_copy = dict(q)          # don't mutate the original
            q_copy["display_num"] = i  # sequential display number
            result.append(q_copy)
        return result

    if mode == "all":
        return all_questions

    if mode == "random_per_segment":
        n = n_per_segment or DEFAULT_QUESTIONS_PER_SEGMENT
        selected = []
        for seg_id in sorted(by_segment.keys()):
            pool = by_segment[seg_id]
            take = min(n, len(pool))
            selected.extend(random.sample(pool, take))
        return selected

    if mode == "random_total":
        n = total_n or len(all_questions)
        return random.sample(all_questions, min(n, len(all_questions)))

    # Default: thirteen_mixed
    return select_questions("thirteen_mixed")


def format_questions_for_display(questions: List[Dict]) -> str:
    """Format questions as plain text using display_num if available."""
    lines = []
    for q in questions:
        num = q.get("display_num", q.get("id", "?"))
        lines.append(f"Q{num}. {q['prompt']}\n")
    return "\n".join(lines)
