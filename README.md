# Torque — AI Car Mechanic Chatbot

A full-stack chatbot where a car owner describes a problem, gets guided
follow-up questions, an AI-assisted diagnosis, and can book a mechanic —
built for the 48-hour Full-Stack Developer Intern task.

**Stack:** Next.js (React) frontend · Django REST Framework + SQLite backend ·
Gemini API used only for diagnosis synthesis and image analysis.

---

## 1. Architecture

```
┌────────────────┐        REST/JSON         ┌──────────────────────┐
│  Next.js (UI)   │ ───────────────────────▶ │  Django REST backend  │
│  Vercel         │ ◀─────────────────────── │  AWS (EC2/Elastic     │
└────────────────┘                           │  Beanstalk) + SQLite  │
                                              └──────────┬────────────┘
                                                          │ only when needed
                                                          ▼
                                                   Gemini API (free tier)
```

**Why it's split this way**

- **Rule engine first, AI last.** `chatbot/rules.py` handles topic filtering
  (is this a car question?), greeting detection, and a keyword-driven
  follow-up-question tree for common symptom categories (won't start,
  noise, overheating, brakes, AC, warning lights). None of that calls
  Gemini. `POST /api/chat/` never touches the AI model.
- **Gemini is called in exactly two places:** `POST /api/diagnosis/`
  (synthesizes the full conversation into a diagnosis) and image uploads
  in `POST /api/upload/` (visual inspection of a photo). Audio/video
  uploads are stored and flagged for technician review rather than run
  through AI, since transcribing/understanding them reliably needs more
  infrastructure than a 48-hour scope allows — noted here rather than
  faked.
- **Graceful degradation.** If `GEMINI_API_KEY` is unset or the API call
  fails for any reason, `gemini_service.py` falls back to a deterministic,
  rule-based diagnosis so the whole flow still works end-to-end without a
  key (useful for grading/demoing without needing credentials).

**Data model:** `Conversation` → has many `Message`s and `MediaUpload`s →
produces `Diagnosis` → optionally produces a `Booking`.

---

## 2. Project structure

```
car-mechanic-chatbot/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── mechanic_backend/        # settings, urls, wsgi/asgi
│   └── chatbot/                 # the one Django app
│       ├── models.py
│       ├── rules.py             # traditional/keyword logic
│       ├── gemini_service.py    # the only place AI is called
│       ├── views.py             # 5 required API endpoints
│       ├── serializers.py
│       └── urls.py
└── frontend/
    ├── app/                     # Next.js App Router (page.js, layout.js, globals.css)
    ├── components/              # MessageBubble, AttachmentControls, BookingModal
    ├── lib/api.js                # fetch wrapper for the backend
    └── .env.local.example
```

---

## 3. Run it locally

### Backend

```bash
cd backend
python -m venv venv

        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# open .env and set SECRET_KEY to any random string.
# leave GEMINI_API_KEY blank to use the rule-based fallback diagnosis,
# or paste a real key from https://aistudio.google.com/app/apikey

python3 manage.py migrate
python3 manage.py createsuperuser   # optional, for /admin/
python3 manage.py runserver          # http://127.0.0.1:8000
```

Libraries installed by `requirements.txt`: `Django`, `djangorestframework`,
`django-cors-headers`, `python-dotenv`, `google-generativeai`, `Pillow`,
`gunicorn`, `whitenoise`.

### Frontend

```bash
cd frontend
npm install

cp .env.local.example .env.local
# NEXT_PUBLIC_API_BASE_URL should point at your backend, e.g.
# http://127.0.0.1:8000/api for local dev

npm run dev    # http://localhost:3000
```

With both running, open `http://localhost:3000`, describe a car problem,
answer the follow-ups, click **Get diagnosis**, then **Book mechanic**.

---

## 4. API documentation

Base URL: `/api/`

### `POST /api/chat/`
Send a chat message; creates a conversation on first call.

Request:
```json
{ "conversation_id": "uuid, omit on first message", "message": "my brakes are squealing" }
```
Response:
```json
{ "conversation_id": "uuid", "bot_reply": "text", "ready_for_diagnosis": false }
```

### `POST /api/upload/`  (multipart/form-data)
Fields: `conversation_id`, `media_type` (`image`/`audio`/`video`), `file`.
Returns the stored `MediaUpload` including an `analysis_note` (AI-generated
for images, a stock note for audio/video).

### `POST /api/diagnosis/`
```json
{ "conversation_id": "uuid" }
```
Returns a `Diagnosis`: `summary`, `probable_causes`, `suggested_repair`,
`confidence`, `used_ai` (whether Gemini or the fallback produced it).

### `POST /api/booking/`
```json
{
  "conversation_id": "uuid",
  "customer_name": "Rushil Sharma",
  "phone_number": "98XXXXXXXX",
  "preferred_date": "2026-10-01",
  "notes": "optional"
}
```
Returns the created `Booking` with its `id` and `status`.

### `GET /api/booking/{id}/`
Returns the current status of a booking.

### `GET /api/conversation/{id}/`  (bonus, used by the frontend for reload)
Returns the conversation with its full message history.

---

## 5. Deploying live

### Backend → AWS free tier (EC2, simplest path)

1. Launch a `t2.micro`/`t3.micro` Ubuntu EC2 instance (free tier eligible).
2. SSH in, install Python 3.11+, then:
   ```bash
   git clone <your-repo-url>
   cd car-mechanic-chatbot/backend
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env   # fill SECRET_KEY, GEMINI_API_KEY, and:
   # DEBUG=False
   # ALLOWED_HOSTS=your-ec2-public-dns-or-ip
   # CORS_ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
3. Run it with Gunicorn behind the instance's security group opened on
   port 8000 (or put Nginx in front on port 80):
   ```bash
   gunicorn mechanic_backend.wsgi:application --bind 0.0.0.0:8000
   ```
   For a persistent process, run this via `systemd` or `tmux`/`screen` so
   it survives your SSH session ending.
4. Open port 8000 (or 80/443 if using Nginx + a domain) in the EC2
   security group. Your live backend URL is `http://<ec2-ip>:8000/api/`.
5. SQLite's file (`db.sqlite3`) lives on the instance's disk — fine for
   this scope; note in your submission that a managed Postgres (RDS free
   tier) would be the production upgrade.

### Frontend → Vercel free tier

1. Push the `frontend/` folder to GitHub (or the whole repo, with
   Vercel's root directory set to `frontend`).
2. Import the repo at [vercel.com/new](https://vercel.com/new).
3. Add an environment variable in the Vercel project settings:
   `NEXT_PUBLIC_API_BASE_URL = http://<your-ec2-ip>:8000/api` (or your
   domain/HTTPS URL).
4. Deploy. Vercel gives you the live frontend URL automatically.
5. Go back to the backend `.env` and set `CORS_ALLOWED_ORIGINS` to the
   exact Vercel URL, then restart Gunicorn.

---

## 6. Notes on AI usage (per the evaluation criteria)

- Topic filtering, greetings, the follow-up question flow, and booking are
  all plain Python/keyword logic — no API calls.
- Gemini is called once per conversation (diagnosis synthesis) and once
  per image upload — never for routine conversational turns.
- Every Gemini call is wrapped in a try/except with a deterministic
  fallback, so a quota limit or bad key degrades the experience instead
  of breaking the app.
