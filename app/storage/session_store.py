"""
Session store: CRUD operations for evaluation sessions.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.storage.database import Session as DbSession, get_session_factory


def create_session(metadata: Dict) -> str:
    """Create a new session record and return its UID."""
    factory = get_session_factory()
    db = factory()
    try:
        uid = str(uuid.uuid4())
        record = DbSession(
            session_uid=uid,
            model_name=metadata.get("model_name", "Unknown"),
            model_version=metadata.get("model_version", ""),
            provider=metadata.get("provider", ""),
            evaluator_name=metadata.get("evaluator_name", ""),
            evaluation_title=metadata.get("evaluation_title", ""),
            notes=metadata.get("notes", ""),
            is_demo=metadata.get("is_demo", False),
        )
        db.add(record)
        db.commit()
        return uid
    finally:
        db.close()


def update_session(session_uid: str, data: Dict) -> bool:
    """Update a session with new data fields."""
    factory = get_session_factory()
    db = factory()
    try:
        record = db.query(DbSession).filter_by(session_uid=session_uid).first()
        if not record:
            return False
        # Map allowed fields
        field_map = {
            "selected_questions": "selected_questions_json",
            "answers": "answers_json",
            "porter_result": "porter_result_json",
            "indicator_scores": "indicator_scores_json",
            "overall_score": "overall_score",
            "adjusted_score": "adjusted_score",
            "reliability_label": "reliability_label",
            "reliability_score": "reliability_score",
            "narrative_summary": "narrative_summary",
            "full_analysis": "full_analysis_json",
        }
        for key, db_field in field_map.items():
            if key in data:
                val = data[key]
                if isinstance(val, (dict, list)):
                    val = json.dumps(val)
                setattr(record, db_field, val)
        record.updated_at = datetime.utcnow()
        db.commit()
        return True
    finally:
        db.close()


def get_session(session_uid: str) -> Optional[Dict]:
    """Load a session by UID as a dict."""
    factory = get_session_factory()
    db = factory()
    try:
        record = db.query(DbSession).filter_by(session_uid=session_uid).first()
        if not record:
            return None
        return _record_to_dict(record)
    finally:
        db.close()


def list_sessions(limit: int = 50) -> List[Dict]:
    """List all sessions ordered by newest first."""
    factory = get_session_factory()
    db = factory()
    try:
        records = (
            db.query(DbSession)
            .order_by(DbSession.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_record_summary(r) for r in records]
    finally:
        db.close()


def delete_session(session_uid: str) -> bool:
    """Delete a session by UID."""
    factory = get_session_factory()
    db = factory()
    try:
        record = db.query(DbSession).filter_by(session_uid=session_uid).first()
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True
    finally:
        db.close()


def _record_to_dict(record: DbSession) -> Dict:
    """Convert a DB record to a full dict, parsing JSON fields."""
    def try_json(val):
        if val is None:
            return None
        try:
            return json.loads(val)
        except Exception:
            return val

    return {
        "id": record.id,
        "session_uid": record.session_uid,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        "model_name": record.model_name,
        "model_version": record.model_version,
        "provider": record.provider,
        "evaluator_name": record.evaluator_name,
        "evaluation_title": record.evaluation_title,
        "notes": record.notes,
        "selected_questions": try_json(record.selected_questions_json),
        "answers": try_json(record.answers_json),
        "porter_result": try_json(record.porter_result_json),
        "indicator_scores": try_json(record.indicator_scores_json),
        "overall_score": record.overall_score,
        "adjusted_score": record.adjusted_score,
        "reliability_label": record.reliability_label,
        "reliability_score": record.reliability_score,
        "narrative_summary": record.narrative_summary,
        "full_analysis": try_json(record.full_analysis_json),
        "is_demo": record.is_demo,
    }


def _record_summary(record: DbSession) -> Dict:
    """Lightweight summary for list view."""
    return {
        "session_uid": record.session_uid,
        "model_name": record.model_name,
        "evaluation_title": record.evaluation_title,
        "overall_score": record.overall_score,
        "reliability_label": record.reliability_label,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "is_demo": record.is_demo,
    }
