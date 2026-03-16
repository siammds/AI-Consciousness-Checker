"""
SQLAlchemy SQLite database models and initialization.
"""
from datetime import datetime
from pathlib import Path
import json
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text,
    DateTime, ForeignKey, Boolean, event
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from app.config import DB_PATH

Base = declarative_base()


class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_uid = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    model_name = Column(String(255))
    model_version = Column(String(100))
    provider = Column(String(100))
    evaluator_name = Column(String(255))
    evaluation_title = Column(String(512))
    notes = Column(Text)
    selected_questions_json = Column(Text)   # JSON list of question IDs
    answers_json = Column(Text)              # JSON dict {qid: answer}
    porter_result_json = Column(Text)        # JSON of Porter scoring (was pointer_result_json)
    indicator_scores_json = Column(Text)     # JSON of 10 indicators
    overall_score = Column(Float)
    adjusted_score = Column(Float)
    reliability_label = Column(String(20))
    reliability_score = Column(Float)
    narrative_summary = Column(Text)
    full_analysis_json = Column(Text)         # Full analysis blob
    is_demo = Column(Boolean, default=False)


def init_db():
    """Initialize the database and create tables. Also handles migrations."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

    # Handle column rename migration (pointer_result_json → porter_result_json)
    # This runs before create_all so existing DBs get the column added
    try:
        with engine.connect() as conn:
            from sqlalchemy import text, inspect
            inspector = inspect(engine)
            cols = [c["name"] for c in inspector.get_columns("sessions")]
            # If old column exists and new doesn't, copy it
            if "pointer_result_json" in cols and "porter_result_json" not in cols:
                conn.execute(text(
                    "ALTER TABLE sessions ADD COLUMN porter_result_json TEXT"
                ))
                conn.execute(text(
                    "UPDATE sessions SET porter_result_json = pointer_result_json"
                ))
                conn.commit()
    except Exception:
        pass  # Table doesn't exist yet — create_all will handle it

    Base.metadata.create_all(engine)
    return engine


def get_engine():
    """Get or create the database engine."""
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    return engine


def get_session_factory():
    """Create and return a session factory."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal
