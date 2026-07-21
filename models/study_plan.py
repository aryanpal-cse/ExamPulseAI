"""
StudyPlan + StudyTask models (Phase 2 / Section 19, 23, 25).

One StudyPlan per (student, subject) — regenerated/adapted over time
rather than duplicated, so "automatically adapt the study plan based on
progress" (Section 19) means updating StudyTask rows under the same plan.
Each StudyTask is one line item like "Graph Theory - 90 minutes" on a
specific day, with a status so the UI can support "mark complete / skip /
reschedule" (Section 19) and the Personal Dashboard's "Today's Mission"
(Section 25).
"""

from datetime import datetime, timezone

from extensions import db

TASK_STATUSES = ("pending", "completed", "skipped", "rescheduled")
TASK_TYPES = ("study_topic", "practice_questions", "revision", "mock_test")


class StudyPlan(db.Model):
    __tablename__ = "study_plans"

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)

    exam_date = db.Column(db.Date, nullable=True)  # snapshot of exam date this plan was built around
    daily_study_minutes = db.Column(db.Integer, nullable=True)  # snapshot of availability this plan was built around

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_adapted_at = db.Column(db.DateTime, nullable=True)  # set whenever the plan auto-adapts to progress

    student_profile = db.relationship("StudentProfile")
    subject = db.relationship("Subject")
    tasks = db.relationship(
        "StudyTask", back_populates="plan", cascade="all, delete-orphan",
        order_by="StudyTask.scheduled_date",
    )

    __table_args__ = (
        db.Index("ix_study_plans_student_subject_active", "student_profile_id", "subject_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<StudyPlan {self.id} student={self.student_profile_id} subject={self.subject_id}>"


class StudyTask(db.Model):
    __tablename__ = "study_tasks"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)

    scheduled_date = db.Column(db.Date, nullable=False, index=True)
    task_type = db.Column(db.String(20), nullable=False, default="study_topic")
    title = db.Column(db.String(200), nullable=False)  # e.g. "Graph Theory"
    duration_minutes = db.Column(db.Integer, nullable=False)

    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    plan = db.relationship("StudyPlan", back_populates="tasks")
    topic = db.relationship("Topic")

    __table_args__ = (
        db.CheckConstraint("status IN " + str(TASK_STATUSES), name="ck_study_task_status"),
        db.CheckConstraint("task_type IN " + str(TASK_TYPES), name="ck_study_task_type"),
    )

    def __repr__(self) -> str:
        return f"<StudyTask {self.title} on {self.scheduled_date}>"
