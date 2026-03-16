"""
FastAPI evaluation routes - the full evaluation pipeline.
"""
import json
import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.services.question_service import select_questions, format_questions_for_display
from app.services.answer_parser import parse_bulk_paste, parse_structured_answers, validate_answers
from app.services.dataset_loader import get_dataset_warnings, get_availability_factor
from app.services.model_runner import get_model_warnings
from app.analysis.word_analysis import analyze_word_choice
from app.analysis.semantic_analysis import analyze_semantic_similarity
from app.analysis.sentiment_analysis import analyze_sentiment
from app.analysis.tone_analysis import analyze_tone
from app.analysis.contradiction_analysis import analyze_contradictions
from app.analysis.dataset_similarity import analyze_dataset_similarity
from app.scoring.scoring_engine import compute_porter_scores, apply_nlp_adjustments, compute_reliability
from app.scoring.indicator_calculator import calculate_indicators
from app.storage.session_store import (
    create_session, update_session, get_session, list_sessions, delete_session
)
from app.exports.exporters import export_json, export_csv, export_html_report
from app.utils.narrative import generate_narrative, generate_strengths_weaknesses
from app.config import PORTER_CREDIT, SCIENTIFIC_DISCLAIMER

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Pydantic Models ─────────────────────────────────────────────────────────

class SessionMetadata(BaseModel):
    model_name: str
    model_version: Optional[str] = ""
    provider: Optional[str] = ""
    evaluator_name: Optional[str] = ""
    evaluation_title: Optional[str] = ""
    notes: Optional[str] = ""


class QuestionRequest(BaseModel):
    mode: str = "thirteen_mixed"
    n_per_segment: Optional[int] = 5
    total_n: Optional[int] = None
    segment_ids: Optional[List[int]] = None


class AnswerSubmission(BaseModel):
    session_uid: str
    answers: Dict[str, str]   # qid (str) → answer text
    bulk_paste: Optional[str] = None
    question_ids: Optional[List[int]] = None


class EvaluateRequest(BaseModel):
    session_uid: str


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/sessions")
async def create_new_session(metadata: SessionMetadata):
    """Create a new evaluation session and return session UID."""
    uid = create_session(metadata.model_dump())
    return {"session_uid": uid, "status": "created"}


@router.post("/questions/generate")
async def generate_questions(req: QuestionRequest):
    """Generate questions. Default mode 'thirteen_mixed' = 1Q from each of 13 random segments."""
    questions = select_questions(
        mode=req.mode,
        n_per_segment=req.n_per_segment,
        total_n=req.total_n,
        segment_ids=req.segment_ids,
    )

    # Flat list for the new inline Q+A UI (display_num is the shown number)
    flat_questions = [
        {
            "id": q["id"],
            "display_num": q.get("display_num", q["id"]),
            "prompt": q["prompt"],
            "segment": q["segment"],
        }
        for q in questions
    ]

    # Legacy grouped list for backward compat
    by_segment: Dict[int, Any] = {}
    for q in questions:
        seg = q["segment"]
        if seg not in by_segment:
            by_segment[seg] = {
                "segment_id": seg,
                "segment_name": q["segment_name"],
                "questions": [],
            }
        by_segment[seg]["questions"].append(q)

    plain_text = format_questions_for_display(questions)

    return {
        "total": len(questions),
        "questions": flat_questions,          # NEW: flat list Q1-Q13
        "segments": list(by_segment.values()),# legacy
        "question_ids": [q["id"] for q in questions],
        "display_nums": {q["id"]: q.get("display_num", q["id"]) for q in questions},
        "plain_text": plain_text,
    }


@router.post("/answers/save")
async def save_answers(submission: AnswerSubmission):
    """Save raw answers to session (structured or parsed from bulk paste)."""
    session_uid = submission.session_uid
    question_ids = submission.question_ids or []

    # Handle bulk paste
    if submission.bulk_paste:
        parsed_answers, confidence = parse_bulk_paste(
            submission.bulk_paste, question_ids
        )
        parse_method = "bulk_paste"
        parser_confidence = confidence
    else:
        # Structured (numbered) answers
        str_answers = {int(k): v for k, v in submission.answers.items()}
        parsed_answers, _ = parse_structured_answers(str_answers)
        parse_method = "structured"
        parser_confidence = 1.0

    # Convert to int keys
    int_answers = {int(k): v for k, v in parsed_answers.items()}
    validation = validate_answers(int_answers, question_ids)

    ok = update_session(session_uid, {"answers": int_answers})
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "saved": len(int_answers),
        "validation": validation,
        "parse_method": parse_method,
        "parser_confidence": round(parser_confidence, 3),
    }


@router.post("/evaluate")
async def evaluate_session(req: EvaluateRequest):
    """
    Run full evaluation pipeline on a saved session.
    Returns all scores, indicators, analysis, narrative, and warnings.
    """
    session = get_session(req.session_uid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load stored data
    raw_answers: Dict = session.get("answers") or {}
    int_answers = {int(k): v for k, v in raw_answers.items()}
    selected_q_ids = session.get("selected_questions") or list(int_answers.keys())

    if not int_answers:
        raise HTTPException(status_code=400, detail="No answers found. Save answers before evaluation.")

    # Load questions for scoring context
    from app.services.question_service import load_question_bank
    all_questions = load_question_bank()
    selected_questions = [q for q in all_questions if q["id"] in int_answers]

    # ── Run all analysis modules ──
    logger.info("Running word analysis...")
    word_analysis = analyze_word_choice(int_answers)

    logger.info("Running semantic analysis...")
    semantic_analysis = analyze_semantic_similarity(int_answers)

    logger.info("Running sentiment analysis...")
    sentiment_analysis = analyze_sentiment(int_answers)

    logger.info("Running tone analysis...")
    tone_analysis = analyze_tone(int_answers)

    logger.info("Running contradiction analysis...")
    contradiction_analysis = analyze_contradictions(int_answers)

    logger.info("Running dataset similarity analysis...")
    dataset_similarity = analyze_dataset_similarity(int_answers)

    # ── Porter Scoring ──
    logger.info("Computing Porter scores...")
    porter_result = compute_porter_scores(int_answers, selected_questions)

    # ── NLP Adjustments ──
    validation = validate_answers(int_answers, [q["id"] for q in selected_questions])
    avg_len = sum(len(t.split()) for t in int_answers.values()) / max(1, len(int_answers))

    adjusted_score, adjustment_log = apply_nlp_adjustments(
        base_score=porter_result["overall_score"],
        contradiction_risk=contradiction_analysis.get("contradiction_risk", 0),
        dataset_similarity=dataset_similarity.get("overall_human_likeness", 0) / 100,
        reflective_density=word_analysis.get("reflective_ratio", 0),
        completeness=validation.get("completeness", 1.0),
    )

    # ── Indicators ──
    indicator_result = calculate_indicators(
        porter_result=porter_result,
        word_analysis=word_analysis,
        semantic_analysis=semantic_analysis,
        sentiment_analysis=sentiment_analysis,
        tone_analysis=tone_analysis,
        contradiction_analysis=contradiction_analysis,
        dataset_similarity=dataset_similarity,
        validation=validation,
        adjusted_score=adjusted_score,
    )

    # ── Reliability ──
    reliability_label, reliability_score = compute_reliability(
        completeness=validation.get("completeness", 1.0),
        dataset_availability=get_availability_factor(),
        contradiction_risk=contradiction_analysis.get("contradiction_risk", 0),
        avg_answer_length=avg_len,
        embedding_available=semantic_analysis.get("embedding_available", False),
    )

    # ── Narrative ──
    narrative = generate_narrative(
        model_name=session.get("model_name", "Unknown Model"),
        adjusted_score=adjusted_score,
        indicators=indicator_result,
        reliability_label=reliability_label,
        contradictions=contradiction_analysis,
        word_analysis=word_analysis,
        tone_analysis=tone_analysis,
    )
    strengths, weaknesses = generate_strengths_weaknesses(indicator_result)

    # ── Collect all warnings ──
    warnings = (
        validation.get("warnings", [])
        + get_dataset_warnings()
        + get_model_warnings()
    )

    # ── Save results ──
    full_analysis = {
        "word_analysis": word_analysis,
        "semantic_analysis": semantic_analysis,
        "sentiment_analysis": sentiment_analysis,
        "tone_analysis": tone_analysis,
        "contradiction_analysis": contradiction_analysis,
        "dataset_similarity": dataset_similarity,
        "adjustment_log": adjustment_log,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "warnings": warnings,
    }

    update_session(req.session_uid, {
        "porter_result": porter_result,
        "indicator_scores": indicator_result,
        "overall_score": porter_result["overall_score"],
        "adjusted_score": adjusted_score,
        "reliability_label": reliability_label,
        "reliability_score": reliability_score,
        "narrative_summary": narrative,
        "full_analysis": full_analysis,
    })

    return {
        "session_uid": req.session_uid,
        "porter_result": porter_result,
        "adjusted_score": adjusted_score,
        "overall_score": porter_result["overall_score"],
        "indicator_scores": indicator_result,
        "reliability_label": reliability_label,
        "reliability_score": round(reliability_score, 3),
        "narrative": narrative,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "word_analysis": word_analysis,
        "semantic_analysis": semantic_analysis,
        "sentiment_analysis": sentiment_analysis,
        "tone_analysis": tone_analysis,
        "contradiction_analysis": contradiction_analysis,
        "dataset_similarity": dataset_similarity,
        "adjustment_log": adjustment_log,
        "warnings": warnings,
        "credit": PORTER_CREDIT,
        "disclaimer": SCIENTIFIC_DISCLAIMER,
    }


@router.get("/sessions")
async def get_sessions():
    """List all saved sessions."""
    return {"sessions": list_sessions()}


@router.get("/sessions/{session_uid}")
async def get_session_detail(session_uid: str):
    """Get full session data."""
    session = get_session(session_uid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_uid}")
async def delete_session_route(session_uid: str):
    """Delete a session."""
    ok = delete_session(session_uid)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}


@router.get("/export/json/{session_uid}")
async def export_session_json(session_uid: str):
    """Export session as JSON."""
    session = get_session(session_uid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    content = export_json(session)
    fname = f"aci_eval_{session_uid[:8]}.json"
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.get("/export/csv/{session_uid}")
async def export_session_csv(session_uid: str):
    """Export session scores as CSV."""
    session = get_session(session_uid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    content = export_csv(session)
    fname = f"aci_eval_{session_uid[:8]}.csv"
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.get("/export/report/{session_uid}")
async def export_session_report(session_uid: str):
    """Generate and return HTML report."""
    session = get_session(session_uid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    content = export_html_report(session)
    return Response(content=content, media_type="text/html")


@router.get("/status")
async def get_status():
    """Return system status including model and dataset availability."""
    from app.services.model_runner import get_model_status
    from app.services.dataset_loader import get_dataset_status
    return {
        "models": get_model_status(),
        "datasets": get_dataset_status(),
        "credit": PORTER_CREDIT,
    }
