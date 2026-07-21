from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    """Public landing page (Section 9 of the spec).

    Full hero content, feature cards, and CTAs are built out visually in
    Phase 18 (Student Dashboard) / templates polish pass. Phase 1 ships a
    functioning route + base layout so the app is runnable end-to-end.
    """
    return render_template("home.html")


@main_bp.route("/healthz")
def healthz():
    """Simple liveness endpoint for Render health checks."""
    return {"status": "ok", "service": "exampulse-ai"}, 200
