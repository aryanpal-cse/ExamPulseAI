"""
ExamPulse AI - Extensions
==========================
Flask extension instances are created here (uninitialized) and bound to the
app later via `init_app()` inside the application factory. This avoids
circular imports between routes/ and models/.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
bcrypt = Bcrypt()

# Login manager configuration
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"
