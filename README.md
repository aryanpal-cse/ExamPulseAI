# ExamPulse AI

**Analyze. Prepare. Practice. Improve.**

An AI-powered personalized exam preparation platform for university
students. ExamPulse AI analyzes historical question papers to surface
important topics, repeated questions, probability-based predictions,
personalized study plans, and an AI Mentor — without requiring any paid
API keys.

> **Build status:** This repo is being built phase-by-phase per the
> development order below. **Phase 1 (project architecture &
> configuration) and Phase 2 (database models) are complete.** Each
> subsequent phase adds services and routes on top of this same structure.

## Phase 1 — what's included

- Flask application factory (`app.py`) with blueprints, error handlers,
  CLI commands (`flask init-db`, `flask seed-db`)
- Environment-driven config (`config.py`) — SQLite locally, Postgres
  (Neon) in production, all via `DATABASE_URL`
- Centralized extensions (`extensions.py`): SQLAlchemy, Migrate,
  Flask-Login, CSRF, Bcrypt
- Minimal `User` model + working register/login/logout
- Landing page matching the product spec's hero + feature cards
- Base Bootstrap layout, error pages (404/500/413)
- `requirements.txt` covering the full stack this project will need
  through later phases (PDF/OCR, NLP/ML, optional Gemini/HF)

## Phase 2 — what's included

Full SQLAlchemy schema for every model in Section 28 of the spec, split
across `models/`:

- `user.py` — `User` (auth only) + `StudentProfile` (1:1, holds all
  onboarding data from Section 8)
- `academic.py` — `University → Course → Branch → Semester → Subject`
  hierarchy, plus `StudentSubject` (which subjects a student is prepping
  for, each with its own exam date)
- `question_paper.py` — `QuestionPaper` (upload + extraction pipeline
  state machine) and `Question` (with duplicate-detection fields)
- `topic.py` — `Topic` (with cached frequency/trend/priority stats) and
  `QuestionTopic` (many-to-many join with confidence score)
- `analysis.py` — `Analysis` (versioned per-subject snapshot, used for
  backtesting) and `Prediction` (probability band + structured reasoning,
  never invented by an LLM)
- `practice.py` — `PracticeQuestion` and `PracticeAttempt`
- `mentor.py` — `MentorConversation` and `MentorMessage` (tracks which
  fallback tier — deterministic / local ML / optional LLM — produced each
  reply)
- `study_plan.py` — `StudyPlan` and `StudyTask`
- `progress.py` — `StudentProgress` (per student/topic mastery) and
  `ExamReadiness` (versioned readiness snapshots with plain-language
  explanations)

All 21 tables, every foreign key, and all 36 `back_populates` relationship
pairs have been mechanically cross-checked for consistency.

## Development order

1. ✅ Project architecture and configuration
2. ✅ Database models
3. Authentication and user profiles (full onboarding)
4. University/course/subject structure
5. Question paper upload and processing
6. Question extraction
7. Topic extraction
8. Similarity and repeated-question detection
9. Frequency and trend analysis
10. Prediction engine
11. Prediction backtesting
12. Practice system
13. Study plan system
14. Progress tracking
15. Exam readiness system
16. Rule-based AI Mentor
17. Optional free-tier AI API enhancement
18. Student dashboard
19. Admin dashboard
20. Testing and deployment

## Local setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit SECRET_KEY at minimum

flask init-db                    # creates SQLite tables
python app.py                    # http://localhost:5000
```

No `DATABASE_URL` needed locally — it defaults to a SQLite file at
`data/exampulse.db`. No `GEMINI_API_KEY` / `HUGGINGFACE_API_KEY` needed
either — the app runs fully on deterministic + local ML logic; those keys
only ever enhance wording later (Phase 17).

## Deployment (Render + Neon)

1. **Neon**: create a Postgres project, copy the connection string.
2. **Render**: create a new Web Service from this repo.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn "app:create_app()"`
   - Environment variables:
     - `DATABASE_URL` = your Neon connection string
     - `SECRET_KEY` = a long random string
     - `FLASK_ENV` = `production`
     - `GEMINI_API_KEY` / `HUGGINGFACE_API_KEY` = optional, leave blank if unused
3. After first deploy, run migrations from the Render shell:
   ```bash
   flask db upgrade   # once Phase 2 introduces Flask-Migrate migrations
   ```

## Project structure

```
exam_pulse_ai/
├── app.py                # application factory
├── config.py              # env-driven configuration
├── extensions.py          # Flask extension instances
├── requirements.txt
├── .env.example
├── routes/                 # blueprints (main, auth, ... added per phase)
├── models/                 # SQLAlchemy models (added per phase)
├── services/                # business logic / NLP / ML / AI mentor
├── data/                    # SQLite db + uploaded papers (gitignored)
├── static/                  # css/js/img
├── templates/                # Jinja2 templates
└── tests/                    # pytest suite
```

## Design principle

Students never see ML/NLP/statistics jargon — only actionable guidance
("Study this first", "Your estimated readiness is 72%"). All prediction
and analytics logic lives in the backend and is explained in plain
language with transparent reasoning ("why was this predicted?").
