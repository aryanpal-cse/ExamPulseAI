"""
Analysis + Prediction models (Phase 2 / Section 16-17).

`Analysis` is a versioned snapshot: every time the analysis engine
(Phase 9) recomputes subject-wide statistics, it writes ONE new Analysis
row rather than mutating the previous one. This is what makes Prediction
Backtesting (Section 17) possible — you can point a backtest at
"the Analysis run as-of papers through 2023" and compare its predictions
against the real 2024 paper without the historical run being overwritten
by later data.

`Prediction` rows always belong to one Analysis run and one Topic, and
always carry `reasoning` (Section 16: "For every prediction show: Why was
this predicted?") — the reasoning is generated from the same deterministic
stats stored on Topic, never invented by an LLM (Section 7/16/26).
"""

from datetime import datetime, timezone

from extensions import db

PROBABILITY_BANDS = ("very_high", "high", "medium", "low")


class Analysis(db.Model):
    """One versioned snapshot of subject-wide analytics."""

    __tablename__ = "analyses"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)

    # The last paper year included in this run — lets backtesting (Phase 11)
    # re-run "as of 2023" analysis and compare against the real 2024 paper.
    papers_included_through_year = db.Column(db.Integer, nullable=True)
    papers_analyzed_count = db.Column(db.Integer, nullable=False, default=0)
    topics_identified_count = db.Column(db.Integer, nullable=False, default=0)
    repeated_questions_count = db.Column(db.Integer, nullable=False, default=0)

    # Backtest results (Section 17), filled in only for analyses that were
    # run specifically to be evaluated against a held-out year.
    is_backtest = db.Column(db.Boolean, nullable=False, default=False)
    backtest_target_year = db.Column(db.Integer, nullable=True)
    backtest_precision = db.Column(db.Float, nullable=True)
    backtest_recall = db.Column(db.Float, nullable=True)
    backtest_f1_score = db.Column(db.Float, nullable=True)
    backtest_topic_coverage = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    subject = db.relationship("Subject")
    predictions = db.relationship("Prediction", back_populates="analysis", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        kind = "backtest" if self.is_backtest else "live"
        return f"<Analysis {kind} subject={self.subject_id} id={self.id}>"


class Prediction(db.Model):
    """
    A single topic's probability-based prediction within one Analysis run.

    IMPORTANT (Section 16): this is never an "exact paper" prediction —
    only a probability band + transparent reasoning for one topic.
    """

    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)

    probability_score = db.Column(db.Float, nullable=False)  # 0-1 continuous score
    probability_band = db.Column(db.String(20), nullable=False, index=True)  # very_high | high | medium | low

    # Structured reasoning factors (Section 16 examples: "Appeared in 8 of
    # last 10 papers", "Has not appeared in the last 2 exams", ...).
    # Stored as JSON so the UI can render a bulleted "Why was this
    # predicted?" list without re-deriving it, while still tracing back to
    # real Topic/Question stats computed elsewhere.
    reasoning = db.Column(db.JSON, nullable=False, default=list)

    # Set only when this Prediction belongs to a backtest Analysis and the
    # target year's paper has been checked against it (Phase 11).
    was_correct = db.Column(db.Boolean, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    analysis = db.relationship("Analysis", back_populates="predictions")
    topic = db.relationship("Topic", back_populates="predictions")

    __table_args__ = (
        db.UniqueConstraint("analysis_id", "topic_id", name="uq_prediction_per_analysis_topic"),
        db.CheckConstraint(
            "probability_band IN " + str(PROBABILITY_BANDS), name="ck_prediction_probability_band"
        ),
    )

    def __repr__(self) -> str:
        return f"<Prediction topic={self.topic_id} band={self.probability_band}>"
