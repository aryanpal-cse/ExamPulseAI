"""
Academic hierarchy models (Phase 2 / Section 10-11 of the spec).

    University -> Course -> Branch -> Semester -> Subject

This mirrors the subject-selection flow exactly:
    AKTU -> B.Tech -> CSE AI & ML -> Semester 3 -> BCS301

The hierarchy is intentionally flexible (Section 3: "architecture must be
flexible enough to support other universities later") — every level is its
own table with its own slug/code, not a hardcoded enum, so new
universities/courses/branches can be added purely as data via the admin
panel (Phase 19) without a schema change.
"""

from datetime import datetime, timezone

from extensions import db


class University(db.Model):
    __tablename__ = "universities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    short_code = db.Column(db.String(20), nullable=False, unique=True, index=True)  # e.g. "AKTU"
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    courses = db.relationship("Course", back_populates="university", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<University {self.short_code}>"


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(
        db.Integer, db.ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = db.Column(db.String(150), nullable=False)  # e.g. "B.Tech"
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    university = db.relationship("University", back_populates="courses")
    branches = db.relationship("Branch", back_populates="course", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("university_id", "name", name="uq_course_per_university"),
    )

    def __repr__(self) -> str:
        return f"<Course {self.name}>"


class Branch(db.Model):
    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)      # e.g. "CSE AI & ML"
    short_code = db.Column(db.String(20), nullable=True)   # e.g. "CSE-AIML"
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    course = db.relationship("Course", back_populates="branches")
    semesters = db.relationship("Semester", back_populates="branch", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("course_id", "name", name="uq_branch_per_course"),
    )

    def __repr__(self) -> str:
        return f"<Branch {self.name}>"


class Semester(db.Model):
    __tablename__ = "semesters"

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    number = db.Column(db.Integer, nullable=False)  # 1-8 typically
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    branch = db.relationship("Branch", back_populates="semesters")
    subjects = db.relationship("Subject", back_populates="semester", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("branch_id", "number", name="uq_semester_per_branch"),
        db.CheckConstraint("number BETWEEN 1 AND 12", name="ck_semester_number_range"),
    )

    def __repr__(self) -> str:
        return f"<Semester {self.number}>"


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    code = db.Column(db.String(20), nullable=False, index=True)   # e.g. "BCS301"
    name = db.Column(db.String(200), nullable=False)               # e.g. "Discrete Structures & Theory of Logic"
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    semester = db.relationship("Semester", back_populates="subjects")
    question_papers = db.relationship("QuestionPaper", back_populates="subject", cascade="all, delete-orphan")
    topics = db.relationship("Topic", back_populates="subject", cascade="all, delete-orphan")
    student_links = db.relationship("StudentSubject", back_populates="subject", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("semester_id", "code", name="uq_subject_code_per_semester"),
    )

    @property
    def display_name(self) -> str:
        return f"{self.code} - {self.name}"

    def __repr__(self) -> str:
        return f"<Subject {self.code}>"


class StudentSubject(db.Model):
    """
    Association between a StudentProfile and the Subjects they're currently
    preparing for, each with its own upcoming exam date (Section 8:
    "Subjects" + "Upcoming exam dates" are both plural/per-subject).

    This is what powers "12 Days Remaining" on the Subject Dashboard
    (Section 11) and the countdown-driven Exam Mode behavior (Section 23).
    """

    __tablename__ = "student_subjects"

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)

    exam_date = db.Column(db.Date, nullable=True)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)  # shown first on dashboard
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    student_profile = db.relationship("StudentProfile", back_populates="subjects")
    subject = db.relationship("Subject", back_populates="student_links")

    __table_args__ = (
        db.UniqueConstraint("student_profile_id", "subject_id", name="uq_student_subject"),
    )

    def __repr__(self) -> str:
        return f"<StudentSubject student_profile_id={self.student_profile_id} subject_id={self.subject_id}>"
