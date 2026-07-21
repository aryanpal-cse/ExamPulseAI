"""
ExamPulse AI - Application Factory
====================================
"Analyze. Prepare. Practice. Improve."

Run locally:
    python app.py

Run with gunicorn (production / Render):
    gunicorn "app:create_app()"
"""

import os

from flask import Flask, render_template

from config import get_config
from extensions import db, migrate, login_manager, csrf, bcrypt


def create_app(env_name: str | None = None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(get_config(env_name))

    _init_extensions(app)
    _ensure_local_dirs(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_cli_commands(app)
    _register_context_processors(app)

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)

    # Import models so Flask-Migrate can detect them. This import must happen
    # after db.init_app() and inside a function to avoid circular imports.
    from models import user  # noqa: F401
    # NOTE: Phase 1 ships only the User model so the app boots end-to-end.
    # academic, question_paper, topic, analysis, prediction, practice,
    # mentor, study_plan, and progress models are added in Phase 2+ and
    # imported here as they land.

    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


def _ensure_local_dirs(app: Flask) -> None:
    """Create local data/upload directories used by SQLite + file uploads."""
    os.makedirs(os.path.join(app.root_path, "data"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def _register_blueprints(app: Flask) -> None:
    from routes.main import main_bp
    from routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    # NOTE: subjects_bp, papers_bp, topics_bp, predictions_bp, practice_bp,
    # study_plan_bp, mentor_bp, progress_bp, admin_bp are registered in
    # later development phases as their route modules are built.


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def file_too_large(e):
        return render_template("errors/413.html"), 413


def _register_cli_commands(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables (dev convenience; use migrations in prod)."""
        db.create_all()
        print("Database tables created.")

    @app.cli.command("seed-db")
    def seed_db():
        """Seed reference data (universities/courses/branches/semesters)."""
        from services.seed import run_seed

        run_seed()
        print("Database seeded.")


def _register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config["APP_NAME"],
            "app_tagline": app.config["APP_TAGLINE"],
        }


# Module-level app instance for `flask run` / gunicorn convenience.
app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False), host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
