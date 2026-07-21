"""
User + StudentProfile models (Phase 2).

`User` handles authentication/authorization only (email, password, role).
Everything about a student's academic context — university, course,
branch, semester, subjects, exam dates, prep level, study time, strong/weak
topics (Section 8 of the spec) — lives on `StudentProfile`, a 1:1 child of
`User`. Keeping these separate means admin/staff accounts never carry
dead student-only columns, and the profile can be re-collected/edited
independently of login credentials (Section 8: "should be able to update
this information later").
"""

from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint

from extensions import db, bcrypt


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # student | admin
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    profile = db.relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("role IN ('student', 'admin')", name="ck_users_role"),
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_active(self) -> bool:  # required by Flask-Login's UserMixin contract
        return self.is_active_account

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class StudentProfile(db.Model):
    """
    One row per student, holding everything from Section 8 (User Onboarding)
    beyond raw login credentials.

    `strong_topics_free_text` / `weak_topics_free_text` capture what the
    student self-reports at onboarding (before the system has any practice
    data of its own). Once PracticeAttempt / StudentProgress rows exist
    (Phase 14), the system's own computed strong/weak topics take priority
    over this self-report — see services/progress.py in that phase.
    """

    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    university_id = db.Column(db.Integer, db.ForeignKey("universities.id"), nullable=True, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"), nullable=True, index=True)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=True, index=True)

    # "Current preparation level" (Section 8) — simple self-reported scale.
    preparation_level = db.Column(db.String(20), nullable=True)  # beginner | intermediate | advanced

    # Minutes/day the student says they can study — drives Phase 13 study plans.
    daily_study_minutes = db.Column(db.Integer, nullable=True)

    strong_topics_free_text = db.Column(db.Text, nullable=True)  # comma-separated, self-reported
    weak_topics_free_text = db.Column(db.Text, nullable=True)    # comma-separated, self-reported

    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User", back_populates="profile")
    university = db.relationship("University")
    course = db.relationship("Course")
    branch = db.relationship("Branch")
    semester = db.relationship("Semester")

    # A student can be preparing for several subjects at once (Section 8:
    # "Subjects" is plural). Backed by the StudentSubject association table
    # defined in models/academic.py so we can attach a per-subject exam date.
    subjects = db.relationship(
        "StudentSubject", back_populates="student_profile", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "preparation_level IN ('beginner', 'intermediate', 'advanced') OR preparation_level IS NULL",
            name="ck_student_profiles_prep_level",
        ),
    )

    def __repr__(self) -> str:
        return f"<StudentProfile user_id={self.user_id}>"
