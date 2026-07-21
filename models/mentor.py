"""
MentorConversation + MentorMessage models (Phase 2 / Section 20-22, 26).

One MentorConversation per (student, subject, mode) thread — switching
Mentor mode (Study/Concept/Exam/Performance/Discipline, Section 22) starts
a new conversation so each mode's history stays coherent, while all of a
student's conversations remain queryable together for "Mentor Memory"
(Section 21).

`used_ai_enhancement` + `data_sources` on MentorMessage exist so the system
can always show/audit whether a given Mentor reply came from Level 1
(deterministic), Level 2 (local ML), or Level 3 (optional external LLM
wording) — required by the fallback hierarchy in Section 31, and by
Section 26's rule that the Mentor must ground answers in real ExamPulse
data, never invented statistics.
"""

from datetime import datetime, timezone

from extensions import db

MENTOR_MODES = ("study", "concept", "exam", "performance", "discipline")
MESSAGE_ROLES = ("student", "mentor")


class MentorConversation(db.Model):
    __tablename__ = "mentor_conversations"

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True, index=True)

    mode = db.Column(db.String(20), nullable=False, default="study")
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_message_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    student_profile = db.relationship("StudentProfile")
    subject = db.relationship("Subject")
    messages = db.relationship(
        "MentorMessage", back_populates="conversation", cascade="all, delete-orphan",
        order_by="MentorMessage.created_at",
    )

    __table_args__ = (
        db.CheckConstraint("mode IN " + str(MENTOR_MODES), name="ck_mentor_conversation_mode"),
    )

    def __repr__(self) -> str:
        return f"<MentorConversation {self.id} mode={self.mode}>"


class MentorMessage(db.Model):
    __tablename__ = "mentor_messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("mentor_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    role = db.Column(db.String(10), nullable=False)  # student | mentor
    content = db.Column(db.Text, nullable=False)

    # Which fallback tier produced a mentor-role message (Section 31).
    used_ai_enhancement = db.Column(db.Boolean, nullable=False, default=False)
    # e.g. ["topic:Graph Theory", "practice_attempts:last_30_days"] — what
    # ExamPulse data grounded this reply, for auditability (Section 26).
    data_sources = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    conversation = db.relationship("MentorConversation", back_populates="messages")

    __table_args__ = (
        db.CheckConstraint("role IN " + str(MESSAGE_ROLES), name="ck_mentor_message_role"),
    )

    def __repr__(self) -> str:
        return f"<MentorMessage {self.role} conv={self.conversation_id}>"
