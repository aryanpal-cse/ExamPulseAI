"""
StudentProgress + ExamReadiness models (Phase 2 / Section 14, 24, 25).

`StudentProgress` is one row per (student, topic) — a running, continually
updated summary derived from PracticeAttempt history (Phase 14 computes
and writes this). It's what lets the system say "Strong Topics: Graph
Theory" / "Needs Attention: Logic" (Section 24/25) without re-scanning
every attempt on every page load.

`ExamReadiness` is a versioned snapshot per (student, subject), similar in
spirit to `Analysis` — every recompute inserts a new row rather than
overwriting, so readiness trend over time can be shown later if desired.
The plain-language `explanation` field is required output (Section 24:
"Provide an explanation... Clearly label this as an estimate").
"""

from datetime import datetime, timezone

from extensions import db

MASTERY_LEVELS = ("weak", "improving", "strong")


class StudentProgress(db.Model):
    __tablename__ = "student_progress"

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)

    attempts_count = db.Column(db.Integer, nullable=False, default=0)
    correct_count = db.Column(db.Integer, nullable=False, default=0)
    average_score = db.Column(db.Float, nullable=True)   # 0-1
    mastery_level = db.Column(db.String(20), nullable=True, index=True)  # weak | improving | strong

    last_practiced_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    student_profile = db.relationship("StudentProfile")
    topic = db.relationship("Topic")

    __table_args__ = (
        db.UniqueConstraint("student_profile_id", "topic_id", name="uq_progress_per_student_topic"),
        db.CheckConstraint(
            "mastery_level IN " + str(MASTERY_LEVELS) + " OR mastery_level IS NULL",
            name="ck_progress_mastery_level",
        ),
    )

    def __repr__(self) -> str:
        return f"<StudentProgress student={self.student_profile_id} topic={self.topic_id}>"


class ExamReadiness(db.Model):
    __tablename__ = "exam_readiness"

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)

    readiness_score = db.Column(db.Float, nullable=False)  # 0-100, e.g. 72.0
    topic_coverage_pct = db.Column(db.Float, nullable=True)
    practice_score_avg = db.Column(db.Float, nullable=True)
    mock_test_score_avg = db.Column(db.Float, nullable=True)
    weak_topic_count = db.Column(db.Integer, nullable=True)
    revision_completion_pct = db.Column(db.Float, nullable=True)

    explanation = db.Column(db.Text, nullable=False)  # e.g. "Your estimated readiness is 72%. Logic is..."

    calculated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    student_profile = db.relationship("StudentProfile")
    subject = db.relationship("Subject")

    __table_args__ = (
        db.Index("ix_exam_readiness_student_subject_time", "student_profile_id", "subject_id", "calculated_at"),
    )

    def __repr__(self) -> str:
        return f"<ExamReadiness {self.readiness_score}% student={self.student_profile_id} subject={self.subject_id}>"
