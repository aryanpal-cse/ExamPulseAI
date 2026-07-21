"""
PracticeQuestion + PracticeAttempt models (Phase 2 / Section 18).

A PracticeQuestion can either be sourced directly from a real extracted
Question (`source_question_id` set — e.g. "Previous Year Question" type)
or generated fresh by the practice-question generation service (Phase 12),
in which case `source_question_id` is null and `is_generated` is True.

PracticeAttempt records every submission a student makes, which is the raw
data behind StudentProgress and ExamReadiness (Phase 14-15) — "the Mentor
must use actual student data" (Section 21).
"""

from datetime import datetime, timezone

from extensions import db

DIFFICULTY_LEVELS = ("easy", "medium", "hard")
PRACTICE_QUESTION_TYPES = ("mcq", "short_answer", "long_answer", "previous_year")


class PracticeQuestion(db.Model):
    __tablename__ = "practice_questions"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)

    # Set when this practice question IS a real previous-year question
    # (Section 18 question type "Previous Year Question"); null when
    # AI/rule-generated.
    source_question_id = db.Column(
        db.Integer, db.ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    is_generated = db.Column(db.Boolean, nullable=False, default=False)

    question_type = db.Column(db.String(20), nullable=False)
    difficulty = db.Column(db.String(10), nullable=False, index=True)

    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=True)          # for MCQ: list of option strings
    correct_answer = db.Column(db.Text, nullable=True)     # answer key / model answer
    explanation = db.Column(db.Text, nullable=True)         # shown after submission (Section 18)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    subject = db.relationship("Subject")
    topic = db.relationship("Topic")
    source_question = db.relationship("Question", back_populates="practice_source")
    attempts = db.relationship("PracticeAttempt", back_populates="practice_question", cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint("difficulty IN " + str(DIFFICULTY_LEVELS), name="ck_practice_question_difficulty"),
        db.CheckConstraint(
            "question_type IN " + str(PRACTICE_QUESTION_TYPES), name="ck_practice_question_type"
        ),
        db.Index("ix_practice_questions_topic_difficulty", "topic_id", "difficulty"),
    )

    def __repr__(self) -> str:
        return f"<PracticeQuestion {self.id} topic={self.topic_id}>"


class PracticeAttempt(db.Model):
    __tablename__ = "practice_attempts"

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    practice_question_id = db.Column(
        db.Integer, db.ForeignKey("practice_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    submitted_answer = db.Column(db.Text, nullable=True)
    is_correct = db.Column(db.Boolean, nullable=True)   # null for ungraded long-answer attempts
    score = db.Column(db.Float, nullable=True)            # 0-1, allows partial credit on long answers
    time_taken_seconds = db.Column(db.Integer, nullable=True)

    attempted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    student_profile = db.relationship("StudentProfile")
    practice_question = db.relationship("PracticeQuestion", back_populates="attempts")

    __table_args__ = (
        db.Index("ix_practice_attempts_student_time", "student_profile_id", "attempted_at"),
    )

    def __repr__(self) -> str:
        return f"<PracticeAttempt student={self.student_profile_id} q={self.practice_question_id}>"
