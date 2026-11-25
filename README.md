# CareCircle Lite

A shared "Today" view for a family coordinating an aging parent's care: who gave the
evening medicine, what's still due, what's overdue, and a quick question box that
summarizes the day.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy 2.0, PostgreSQL, pytest
- **Frontend:** React + TypeScript (Vite), plain CSS (no UI framework)
- **Streaming:** Server-Sent Events (SSE) for the "Ask about today" assistant
- **Infra:** Docker Compose (Postgres + API + static web server)

## Running it

### One command (Docker)

```bash
docker compose up --build
```

This starts Postgres, the API on `http://localhost:8000`, and the UI on
`http://localhost:4173`. On first boot the API seeds one demo family ("Amma", cared for
by Ravi and Priya) with a mix of overdue/due/done tasks so the app isn't empty.

Optional: copy `.env.example` to `.env` and set `GROQ_API_KEY` if you want the
assistant's answer phrased by an LLM (Groq's free tier) instead of the built-in
template. Not required — the template path is the default and needs no key.

To wipe the demo data and reseed: `docker compose down -v && docker compose up --build`.

### Manual, without Docker

Backend (needs Python 3.10+ and a running Postgres):

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://carecircle:carecircle@localhost:5432/carecircle
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173, talks to the API on :8000
```

### Tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```

15 tests, run against an in-memory SQLite database (no Postgres needed to test):
- `tests/test_grouping.py` — the overdue/due/done sorting logic, in isolation, with no DB
- `tests/test_tasks_api.py` — the `/tasks` and `/tasks/today` endpoints end-to-end,
  including the concurrent "two people tap done at once" case
- `tests/test_assistant.py` — the template answer builder

## Design notes

**Data model.** `CareRecipient` (the parent), `FamilyMember`, `CareTask` (medicine /
appointment / checkin / other, with a `due_at` and `pending`/`done` status), and
`AIInteraction` (one row per assistant question, logged for review). All timestamps are
stored as naive UTC and re-stamped with an explicit UTC offset on the way out, so the
browser never misreads them as local time.

**"Today" grouping.** A task is `overdue` once its `due_at` has passed and it's still
pending; otherwise it's `due`. This logic lives in `app/grouping.py` as a pure function
over plain objects — no DB, no ORM — specifically so it can be unit tested directly
(see `test_grouping.py`) rather than only through the API.

**Two people, one task.** The brief's "handling two people marking done at once" is
solved without any locking infrastructure: `complete_task` issues a single conditional
`UPDATE ... WHERE status = 'pending'`. Whoever's request reaches Postgres first flips
the row; the second request affects zero rows and gets a `409`, which the UI shows as
"someone else just did that" instead of silently overwriting who-did-it.

**No real auth.** Family members pick their name from a dropdown ("I am: Ravi") instead
of logging in — the brief's main requirement is recording *who* completed a task, not
authenticating them. That name is remembered in `localStorage` so a caregiver doesn't
re-pick it every visit. Swapping this for real auth would mean adding a login endpoint
and checking a session/JWT instead of trusting the posted `completed_by_id` — the rest
of the data model doesn't change.

**The assistant.** `/assistant/ask` streams Server-Sent Events. By default it builds the
answer from a deterministic template over the day's tasks (see `app/assistant.py`) — no
API key, no network call, and the exact wording the brief's example shows ("Mum's 8pm BP
tablet is still pending; Ravi did the 9am one"). If `GROQ_API_KEY` is set, it instead
streams from Groq's chat-completions API with the same task context as the prompt, and
falls back to the template if that call fails for any reason. Every question — context
sent, full answer, latency — is logged to `ai_interactions` either way.

**Nice-to-haves done:** the concurrent-completion handling above, and basic voice input
for the assistant box (Web Speech API, when the browser supports it — Chrome does,
Firefox doesn't, so the mic button only appears when available).

**Nice-to-haves skipped, deliberately:** real login and public deployment. Both are
mechanical rather than interesting given the time budget, and the brief says to pick a
few, not all.

## API

| Method | Path | Purpose |
|---|---|---|
| `POST/GET` | `/recipients` | create / list care recipients |
| `POST/GET` | `/family-members` | create / list family members |
| `POST/GET` | `/tasks` | create a task / list tasks |
| `GET` | `/tasks/today?recipient_id=` | today's tasks grouped into overdue/due/done |
| `PATCH` | `/tasks/{id}` | edit a task |
| `POST` | `/tasks/{id}/complete` | mark done (`{completed_by_id}`); `409` if already done |
| `POST` | `/assistant/ask` | SSE stream of the answer to a question |
| `GET` | `/assistant/logs` | review past assistant Q&A, context, and latency |

## Tools used

Built with **Claude Code** (Sonnet) as a pair-programming assistant for essentially the
whole project: scaffolding the FastAPI app and SQLAlchemy models, writing the React
components and CSS, drafting the pytest suite, and the Docker/Compose setup. I reviewed
and understand every file; the one real bug Claude Code introduced and then caught
itself was a naive-vs-timezone-aware `datetime` mismatch that only showed up against
real Postgres (SQLite silently tolerated it) — caught by actually running
`docker compose up` and hitting the API, not just by reading the code. No other AI
tools were used.

## Known limitations

- Single hard-coded family (whichever recipient is seeded first) — there's no UI to
  create additional recipients, though the endpoint exists.
- No migrations tool (Alembic); the schema is created with `Base.metadata.create_all`
  on startup. Fine for this exercise, not what I'd ship to production.
- "Today" is a UTC calendar day server-side, not the caregiver's local day — fine for
  one timezone-local family, worth revisiting for a distributed one.
