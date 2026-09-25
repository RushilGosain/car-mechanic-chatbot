# 🔧 Torque — AI Car Mechanic Chatbot


Torque is a full-stack AI-assisted car mechanic chatbot that helps car owners describe vehicle problems, answer guided follow-up questions, receive a probable diagnosis, upload supporting images, and book a mechanic.

The application is designed with a **rule-engine-first architecture**, using AI only where it adds meaningful value. This keeps routine conversations fast, predictable, and cost-efficient while still using Gemini for diagnosis synthesis and image analysis.

---

## 🚗 Project Overview

When a car owner experiences a problem, they may not know what information is important to provide to a mechanic.

Torque solves this by providing a conversational workflow:

```text
User describes car problem
          ↓
Topic & symptom detection
          ↓
Guided follow-up questions
          ↓
Conversation analysis
          ↓
AI-assisted diagnosis
          ↓
Probable causes + suggested repair
          ↓
Book a mechanic
```

The application supports common vehicle issues such as:

* 🚘 Car won't start
* 🔊 Unusual noises
* 🌡️ Engine overheating
* 🛑 Brake problems
* ❄️ AC problems
* ⚠️ Warning lights
* 🔧 Other common vehicle-related symptoms

---

# ✨ Key Features

### 💬 Intelligent Chat Flow

Users can describe their car problem naturally through a conversational interface.

The application identifies common automotive symptoms and asks relevant follow-up questions before generating a diagnosis.

### 🧠 Rule-Based Conversation Engine

Routine conversation does not require an AI API call.

The backend contains a rule engine responsible for:

* Detecting whether the query is car-related
* Greeting detection
* Identifying common symptom categories
* Selecting relevant follow-up questions
* Determining when enough information has been collected

This makes the chatbot faster and reduces unnecessary AI API usage.

### 🤖 AI-Assisted Diagnosis

Once the required information has been collected, Gemini is used to synthesize the conversation into:

* Diagnosis summary
* Probable causes
* Suggested repair
* Confidence level

### 🖼️ Image Analysis

Users can upload an image related to their car problem.

Gemini can analyze supported images and provide an inspection note that can assist with the diagnosis.

### 📎 Media Uploads

The application supports:

* Images
* Audio
* Video

Images are analyzed using AI.

Audio and video files are stored and flagged for technician review rather than pretending to provide unsupported AI analysis.

### 👨‍🔧 Mechanic Booking

After receiving a diagnosis, users can book a mechanic by providing:

* Customer name
* Phone number
* Preferred date
* Additional notes

The booking is stored in the backend and receives a booking ID and status.

### 🔄 Conversation Persistence

Conversations, messages, media uploads, diagnoses, and bookings are stored in the backend.

The frontend can also reload an existing conversation using the conversation endpoint.

### 🛡️ Graceful AI Fallback

The application does not completely depend on Gemini.

If:

* The Gemini API key is missing
* The API request fails
* The API quota is unavailable
* Another AI-related error occurs

the backend falls back to a deterministic rule-based diagnosis.

This allows the complete application flow to continue working without an active AI API key.

---

# 🏗️ Architecture

```text
┌─────────────────────────┐
│                         │
│      Next.js Frontend   │
│        React UI         │
│                         │
└────────────┬────────────┘
             │
             │ REST / JSON
             ▼
┌─────────────────────────┐
│                         │
│    Django REST API      │
│                         │
│  ┌───────────────────┐  │
│  │   Rule Engine     │  │
│  │                   │  │
│  │ Topic Detection   │  │
│  │ Follow-ups        │  │
│  │ Greetings         │  │
│  └───────────────────┘  │
│                         │
│  ┌───────────────────┐  │
│  │   Gemini Service  │  │
│  │                   │  │
│  │ Diagnosis         │  │
│  │ Image Analysis    │  │
│  └───────────────────┘  │
│                         │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│        SQLite DB        │
│                         │
│ Conversations           │
│ Messages                │
│ Media Uploads           │
│ Diagnoses               │
│ Bookings                │
└─────────────────────────┘
```

---

# 🧩 Architecture Decisions

## 1. Rule Engine First, AI Last

One of the main design decisions was to avoid sending every user message to Gemini.

The file:

```text
backend/chatbot/rules.py
```

handles:

* Topic filtering
* Greeting detection
* Symptom classification
* Follow-up questions
* Conversation flow

Therefore:

```text
POST /api/chat/
```

does **not** call Gemini.

This reduces:

* API usage
* Response latency
* AI costs
* Unnecessary model dependency

---

## 2. Gemini Only Where AI Adds Value

Gemini is used in two primary situations:

### Diagnosis

```text
POST /api/diagnosis/
```

The complete conversation is passed to the Gemini service to generate an AI-assisted diagnosis.

### Image Analysis

```text
POST /api/upload/
```

When the uploaded media is an image, Gemini can analyze the image and generate an inspection note.

---

## 3. Graceful Degradation

AI services can fail because of:

* API limits
* Invalid API keys
* Network problems
* Service availability

Therefore, Gemini calls are wrapped with error handling.

If Gemini fails, the application uses a deterministic fallback diagnosis instead of breaking the user flow.

---

# 🗂️ Data Model

The application follows the following relationship:

```text
Conversation
     │
     ├── Messages
     │
     ├── MediaUploads
     │
     └── Diagnosis
             │
             └── Booking
```

### Conversation

Stores the user's active chatbot session.

### Message

Stores user and bot messages associated with a conversation.

### MediaUpload

Stores uploaded image, audio, or video files.

### Diagnosis

Stores:

* Summary
* Probable causes
* Suggested repair
* Confidence
* Whether AI was used

### Booking

Stores mechanic booking information and booking status.

---

# 🛠️ Tech Stack

## Frontend

| Technology | Purpose                   |
| ---------- | ------------------------- |
| Next.js    | Frontend framework        |
| React      | UI development            |
| JavaScript | Application logic         |
| CSS        | Styling and responsive UI |

## Backend

| Technology            | Purpose           |
| --------------------- | ----------------- |
| Django                | Backend framework |
| Django REST Framework | REST APIs         |
| Python                | Backend logic     |
| SQLite                | Database          |
| Gunicorn              | Production server |

## AI

| Technology        | Purpose             |
| ----------------- | ------------------- |
| Google Gemini API | Diagnosis synthesis |
| Google Gemini API | Image analysis      |

## Development

| Tool   | Purpose             |
| ------ | ------------------- |
| Git    | Version control     |
| GitHub | Repository hosting  |
| Vercel | Frontend deployment |
| AWS    | Backend deployment  |

---

# 📁 Project Structure

```text
car-mechanic-chatbot/
│
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── mechanic_backend/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   └── chatbot/
│       ├── models.py
│       ├── rules.py
│       ├── gemini_service.py
│       ├── views.py
│       ├── serializers.py
│       └── urls.py
│
└── frontend/
    ├── app/
    │   ├── page.js
    │   ├── layout.js
    │   └── globals.css
    │
    ├── components/
    │   ├── MessageBubble
    │   ├── AttachmentControls
    │   └── BookingModal
    │
    └── lib/
        └── api.js
```

---

# 🔌 API Documentation

Base URL:

```text
/api/
```

## 1. Chat

### `POST /api/chat/`

Sends a message to the chatbot and continues the guided conversation.

### Request

```json
{
  "conversation_id": "uuid",
  "message": "My brakes are making a squealing noise"
}
```

`conversation_id` can be omitted for the first message.

### Response

```json
{
  "conversation_id": "uuid",
  "bot_reply": "How long have you been experiencing the squealing?",
  "ready_for_diagnosis": false
}
```

---

## 2. Upload Media

### `POST /api/upload/`

Uploads an image, audio, or video associated with a conversation.

### Content Type

```text
multipart/form-data
```

### Fields

```text
conversation_id
media_type
file
```

Supported media types:

```text
image
audio
video
```

For images, Gemini can provide an AI-generated analysis note.

Audio and video uploads are stored for technician review.

---

## 3. Generate Diagnosis

### `POST /api/diagnosis/`

Generates a diagnosis from the collected conversation.

### Request

```json
{
  "conversation_id": "uuid"
}
```

### Response

```json
{
  "summary": "The symptoms are consistent with worn brake pads.",
  "probable_causes": [
    "Worn brake pads",
    "Brake rotor surface wear"
  ],
  "suggested_repair": "Inspect the brake pads and rotors and replace worn components.",
  "confidence": 0.85,
  "used_ai": true
}
```

---

## 4. Book Mechanic

### `POST /api/booking/`

Creates a mechanic booking.

### Request

```json
{
  "conversation_id": "uuid",
  "customer_name": "Customer Name",
  "phone_number": "98XXXXXXXX",
  "preferred_date": "2026-10-01",
  "notes": "Optional notes"
}
```

### Response

Returns the created booking with:

* Booking ID
* Booking status
* Customer details
* Preferred date

---

## 5. Get Booking Status

### `GET /api/booking/{id}/`

Returns the current status of a mechanic booking.

---

## 6. Get Conversation

### `GET /api/conversation/{id}/`

Returns the conversation and its message history.

This endpoint is also used by the frontend to restore a conversation after reload.

---

# 🖥️ Screenshots

## 1. Chat Interface

The main chatbot interface where users describe their vehicle problem and answer guided follow-up questions.

![Torque Chat Interface]
 <img width="1470" height="804" alt="Screenshot 2026-09-25 at 1 09 13 AM" src="https://github.com/user-attachments/assets/1f09cbeb-7bc6-4345-8462-e3ae5a218448" />


---

## 2. AI Diagnosis

The diagnosis screen showing the probable issue, possible causes, suggested repair, and confidence.

![Torque AI Diagnosis]
 <img width="1470" height="804" alt="Screenshot 2026-09-25 at 1 09 50 AM" src="https://github.com/user-attachments/assets/7d42524e-7f2f-4816-bf1e-c80ac30070b7" />
 

---

## 3. Mechanic Booking

The mechanic booking interface where users provide their details and preferred appointment date.

![Torque Mechanic Booking]
<img width="1470" height="804" alt="Screenshot 2026-09-25 at 1 10 40 AM" src="https://github.com/user-attachments/assets/e6e2e488-68c9-4898-b6f7-3917a6afa8f3" />
 


---

# 🚀 Running the Project Locally

## Prerequisites

Make sure the following are installed:

* Python 3.11+
* Node.js
* npm
* Git

---

## Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it.

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

```bash
cp .env.example .env
```

Configure the `.env` file:

```env
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
```

Run migrations:

```bash
python3 manage.py migrate
```

Start the Django server:

```bash
python3 manage.py runserver
```

Backend will run at:

```text
http://127.0.0.1:8000
```

---

# 💻 Frontend Setup

Open another terminal and navigate to:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create the environment file:

```bash
cp .env.local.example .env.local
```

Set the API URL:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api
```

Start the development server:

```bash
npm run dev
```

The frontend will run at:

```text
http://localhost:3000
```

---

# 🔐 Environment Variables

## Backend

```env
SECRET_KEY=
GEMINI_API_KEY=
DEBUG=
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=
```

## Frontend

```env
NEXT_PUBLIC_API_BASE_URL=
```

API keys and secret credentials should **never be committed to GitHub**.

Use `.env.example` files to document required variables without exposing actual credentials.

---

# 🌐 Deployment

## Frontend

The Next.js frontend can be deployed using Vercel.

The frontend requires:

```env
NEXT_PUBLIC_API_BASE_URL=<production-backend-url>/api
```

## Backend

The Django REST backend can be deployed using an AWS EC2 instance with Gunicorn.

Example production command:

```bash
gunicorn mechanic_backend.wsgi:application --bind 0.0.0.0:8000
```

For a production deployment, the recommended architecture would include:

```text
Internet
   │
   ▼
Nginx / HTTPS
   │
   ▼
Gunicorn
   │
   ▼
Django REST Framework
   │
   ├── PostgreSQL
   │
   └── Gemini API
```

SQLite is sufficient for the scope of this assignment. A managed PostgreSQL database would be a suitable production upgrade.

---

# 🤖 AI Usage

AI was intentionally limited to areas where it provides meaningful value.

| Feature                | AI Used? |
| ---------------------- | -------- |
| Greeting detection     | ❌        |
| Topic filtering        | ❌        |
| Symptom classification | ❌        |
| Follow-up questions    | ❌        |
| Conversation handling  | ❌        |
| Diagnosis synthesis    | ✅ Gemini |
| Image analysis         | ✅ Gemini |
| Booking                | ❌        |
| Booking status         | ❌        |

This approach avoids unnecessary AI calls during normal conversation.

### AI Call Strategy

```text
User Message
     │
     ▼
Rule Engine
     │
     ├── Common conversation → No AI
     │
     └── Diagnosis required
              │
              ▼
          Gemini API
              │
              ▼
        Structured Diagnosis
```

---

# ⚠️ Limitations

The application was developed within the scope and time constraints of the assignment.

Current limitations include:

* Diagnosis is intended as an initial AI-assisted assessment, not a replacement for professional mechanical inspection.
* Audio and video files are stored for technician review rather than processed by AI.
* SQLite is suitable for the current assignment scope but would be replaced with a managed relational database for a larger production deployment.
* Authentication and role-based access can be expanded for a production mechanic/customer platform.
* File storage can be migrated to object storage such as Amazon S3 for production usage.

---

# 🔮 Future Improvements

Potential production improvements include:

* 👤 Customer and mechanic authentication
* 👨‍🔧 Mechanic dashboard
* 📅 Real-time mechanic availability
* 📍 Location-based mechanic matching
* 🔔 Booking notifications
* 💳 Online payments
* 🗄️ PostgreSQL / managed database
* ☁️ S3-based media storage
* 🎙️ Speech-to-text for audio uploads
* 🎥 Video analysis
* 📊 Admin analytics dashboard
* 🔐 More granular authentication and authorization
* 🚀 Background processing for AI and media tasks

---

# 🧪 Testing

The API endpoints can be tested using tools such as Postman.

The primary flow to test is:

```text
POST /api/chat/
        ↓
POST /api/chat/
        ↓
POST /api/upload/
        ↓
POST /api/diagnosis/
        ↓
POST /api/booking/
        ↓
GET /api/booking/{id}/
```

The frontend also consumes the same REST APIs through the API wrapper located at:

```text
frontend/lib/api.js
```

---

# 📌 Assignment Requirements Covered

| Requirement                | Implementation                           |
| -------------------------- | ---------------------------------------- |
| Full-stack application     | Next.js + Django REST                    |
| Conversational interface   | Rule-based chatbot                       |
| Guided follow-up questions | Symptom-specific question tree           |
| AI diagnosis               | Gemini API                               |
| Image analysis             | Gemini API                               |
| Media uploads              | Image / Audio / Video                    |
| Mechanic booking           | Booking API + UI                         |
| Persistent data            | SQLite + Django models                   |
| REST APIs                  | Django REST Framework                    |
| Error handling             | Gemini fallback mechanism                |
| Responsive frontend        | Next.js UI                               |
| Documentation              | API + architecture + setup documentation |

---

# 👨‍💻 Developer

**Rushil Gosain**

B.Tech — Computer Science & Engineering

### GitHub

https://github.com/RushilGosain

### Portfolio

https://rushil-ai-portfolio.netlify.app/

### Project Repository

https://github.com/RushilGosain/car-mechanic-chatbot

---

# 📄 License

This project was developed as part of a **Full-Stack Development Internship assignment for Instant Mechanic**.
