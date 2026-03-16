"""Tests for session storage."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def setup_db():
    from app.storage.database import init_db
    init_db()


def test_create_and_get_session():
    setup_db()
    from app.storage.session_store import create_session, get_session
    uid = create_session({"model_name": "TestAI", "is_demo": False})
    assert uid is not None
    session = get_session(uid)
    assert session is not None
    assert session["model_name"] == "TestAI"


def test_update_session():
    setup_db()
    from app.storage.session_store import create_session, update_session, get_session
    uid = create_session({"model_name": "UpdateTestAI"})
    ok = update_session(uid, {"overall_score": 75.5, "reliability_label": "High"})
    assert ok
    session = get_session(uid)
    assert session["overall_score"] == 75.5
    assert session["reliability_label"] == "High"


def test_list_sessions():
    setup_db()
    from app.storage.session_store import list_sessions
    sessions = list_sessions()
    assert isinstance(sessions, list)


def test_delete_session():
    setup_db()
    from app.storage.session_store import create_session, delete_session, get_session
    uid = create_session({"model_name": "DeleteTestAI"})
    ok = delete_session(uid)
    assert ok
    session = get_session(uid)
    assert session is None
