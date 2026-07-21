"""
User model (Phase 1 placeholder).

This minimal version exists so the app factory, Flask-Login, and blueprints
import cleanly starting in Phase 1. It is expanded into the full User +
StudentProfile relationship set in Phase 2 (Database Models) and Phase 3
(Authentication and user profiles).
"""

from datetime import datetime, timezone

from flask_login import UserMixin

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

    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self) -> bool:  # required by Flask-Login's UserMixin contract
        return self.is_active_account

    def __repr__(self) -> str:
        return f"<User {self.email}>"
