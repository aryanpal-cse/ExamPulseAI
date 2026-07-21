"""
Topic + QuestionTopic models (Phase 2 / Section 13-15).

Topic is per-subject (not global) — "Graph Theory" in Discrete Structures
is a different row than any similarly-named topic elsewhere, which keeps
frequency/marks stats scoped correctly per subject.

QuestionTopic is the many-to-many join between Question and Topic (one
question can touch multiple topics, e.g. a question spanning both "Graph
Theory" and "Trees"), with a per-link confidence score from the topic
extraction service (Phase 7) since topic tagging is probabilistic, not
guaranteed.

The cached aggregate columns on Topic (`total_appearances`,
`recent_appearances`, `total_marks`, `trend`) are written by the
frequency/trend analysis service (Phase 9) — they are denormalized on
purpose so the Subject Dashboard and Important Topics page (Sections 11 &
13) can render instantly without recomputing aggregates on every request.
"""

from datetime import datetime, timezone

from extensions import db

PRIORITY_LEVELS = ("very_important", "important", "moderate", "low_priority")
TREND_DIRECTIONS = ("increasing", "stable", "decreasing", "unknown")


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)

    name = db.Column(db.String(200), nullable=False)
    unit_number = db.Column(db.Integer, nullable=True, index=True)

    # --- Cached analytics (written by services/analysis.py, Phase 9) --------
    total_appearances = db.Column(db.Integer, nullable=False, default=0)
    recent_appearances = db.Column(db.Integer, nullable=False, default=0)  # last N papers, N set by service
    total_marks = db.Column(db.Float, nullable=False, default=0.0)
    trend = db.Column(db.String(20), nullable=False, default="unknown")
    priority_level = db.Column(db.String(20), nullable=True, index=True)
    stats_updated_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    subject = db.relationship("Subject", back_populates="topics")
    question_links = db.relationship("QuestionTopic", back_populates="topic", cascade="all, delete-orphan")
    predictions = db.relationship("Prediction", back_populates="topic", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("subject_id", "name", name="uq_topic_per_subject"),
        db.CheckConstraint(
            "priority_level IN " + str(PRIORITY_LEVELS) + " OR priority_level IS NULL",
            name="ck_topic_priority_level",
        ),
        db.CheckConstraint("trend IN " + str(TREND_DIRECTIONS), name="ck_topic_trend"),
    )

    def __repr__(self) -> str:
        return f"<Topic {self.name} (subject={self.subject_id})>"


class QuestionTopic(db.Model):
    __tablename__ = "question_topics"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)

    confidence = db.Column(db.Float, nullable=False, default=1.0)  # 0-1, from topic extraction (Phase 7)
    is_manually_verified = db.Column(db.Boolean, nullable=False, default=False)

    question = db.relationship("Question", back_populates="topic_links")
    topic = db.relationship("Topic", back_populates="question_links")

    __table_args__ = (
        db.UniqueConstraint("question_id", "topic_id", name="uq_question_topic"),
    )

    def __repr__(self) -> str:
        return f"<QuestionTopic q={self.question_id} t={self.topic_id}>"
