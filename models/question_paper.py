"""
QuestionPaper + Question models (Phase 2 / Section 12).

A QuestionPaper is one uploaded PDF/image. It moves through the pipeline:

    uploaded -> extracting -> extracted -> verified -> failed

Question rows are only created by the extraction service (Phase 6), but the
`extraction_status` state machine and `verified_by` audit field are modeled
now so later phases have somewhere to write.
"""

from datetime import datetime, timezone

from extensions import db

EXTRACTION_STATUSES = ("uploaded", "extracting", "extracted", "verified", "failed")
QUESTION_TYPES = ("mcq", "short_answer", "long_answer", "numerical", "other")


class QuestionPaper(db.Model):
    __tablename__ = "question_papers"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    year = db.Column(db.Integer, nullable=True, index=True)   # exam year, e.g. 2024
    exam_term = db.Column(db.String(50), nullable=True)         # e.g. "End Semester", "Mid Term 1"

    original_filename = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(500), nullable=False)     # path under UPLOAD_FOLDER
    file_type = db.Column(db.String(10), nullable=False)         # pdf | png | jpg | jpeg
    page_count = db.Column(db.Integer, nullable=True)

    extraction_status = db.Column(db.String(20), nullable=False, default="uploaded", index=True)
    extraction_notes = db.Column(db.Text, nullable=True)         # errors / OCR confidence notes

    verified_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    subject = db.relationship("Subject", back_populates="question_papers")
    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_user_id])
    verified_by = db.relationship("User", foreign_keys=[verified_by_user_id])
    questions = db.relationship("Question", back_populates="paper", cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint(
            "extraction_status IN " + str(EXTRACTION_STATUSES), name="ck_paper_extraction_status"
        ),
    )

    def __repr__(self) -> str:
        return f"<QuestionPaper {self.original_filename} ({self.year})>"


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.Integer, db.ForeignKey("question_papers.id", ondelete="CASCADE"), nullable=False, index=True)

    question_number = db.Column(db.String(20), nullable=True)   # e.g. "Q1(a)"
    unit_number = db.Column(db.Integer, nullable=True, index=True)
    marks = db.Column(db.Float, nullable=True)
    question_type = db.Column(db.String(20), nullable=False, default="other")

    raw_text = db.Column(db.Text, nullable=False)                 # as extracted, before cleaning
    cleaned_text = db.Column(db.Text, nullable=True)               # normalized text used for NLP (Phase 6/7)

    # Populated by the similarity-detection service (Phase 8) once it has
    # run: points to the "canonical" question this one is a repeat/near-dup
    # of, so a family of repeated questions can be queried in one join
    # instead of re-computing similarity every time.
    duplicate_of_question_id = db.Column(
        db.Integer, db.ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    similarity_score = db.Column(db.Float, nullable=True)  # 0-1, similarity to duplicate_of_question_id

    is_verified = db.Column(db.Boolean, nullable=False, default=False)  # admin-confirmed extraction (Section 12)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    paper = db.relationship("QuestionPaper", back_populates="questions")
    duplicate_of = db.relationship("Question", remote_side=[id])
    topic_links = db.relationship("QuestionTopic", back_populates="question", cascade="all, delete-orphan")
    practice_source = db.relationship(
        "PracticeQuestion", back_populates="source_question", uselist=False
    )

    __table_args__ = (
        db.CheckConstraint(
            "question_type IN " + str(QUESTION_TYPES), name="ck_question_type"
        ),
        db.Index("ix_questions_paper_unit", "paper_id", "unit_number"),
    )

    def __repr__(self) -> str:
        return f"<Question {self.id} paper={self.paper_id}>"
