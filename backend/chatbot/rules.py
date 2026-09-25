"""
Traditional (non-AI) logic for the mechanic chatbot.

Per the task brief, this module keeps the bot on-topic and drives the
follow-up questions using plain keyword/state rules. Gemini is only
invoked for the final diagnosis synthesis (see gemini_service.py), and
only after this rule engine decides enough information exists.
"""
import re

CAR_KEYWORDS = [
    "car", "engine", "brake", "brakes", "tyre", "tire", "clutch", "gear",
    "transmission", "battery", "alternator", "radiator", "coolant",
    "oil", "exhaust", "muffler", "suspension", "steering", "wheel",
    "ac", "air conditioner", "headlight", "dashboard", "warning light",
    "check engine", "starter", "spark plug", "fuel", "petrol", "diesel",
    "vibration", "noise", "smoke", "overheat", "stall", "mileage",
    "wiper", "horn", "vehicle", "bike", "motorcycle", "bonnet", "hood",
]

GREETING_WORDS = ["hi", "hello", "hey", "namaste", "good morning", "good evening"]

OFF_TOPIC_REPLY = (
    "I'm your virtual auto mechanic, so I can only help with car and vehicle "
    "issues — engine, brakes, electrical, noises, warning lights, and so on. "
    "Could you tell me what's going on with your vehicle?"
)

GREETING_REPLY = (
    "Hi, I'm your virtual mechanic. Tell me what's happening with your car — "
    "any noise, warning light, or issue you've noticed — and I'll help you "
    "figure out what's wrong."
)

# Symptom -> ordered list of rule-based follow-up questions.
# The bot walks this list before ever calling the AI model.
SYMPTOM_TREES = {
    "wont_start": {
        "keywords": ["won't start", "wont start", "not starting", "doesn't start", "no start", "cranking"],
        "questions": [
            "When you turn the key, does the engine crank at all, or is there total silence?",
            "Do the dashboard lights and headlights come on normally?",
            "How old is the battery, and was it recently jump-started?",
        ],
    },
    "noise": {
        "keywords": ["noise", "sound", "squeak", "grinding", "knocking", "rattling", "clicking"],
        "questions": [
            "Where does the noise seem to come from — engine bay, wheels, or underneath?",
            "Does it happen while driving, braking, turning, or at idle?",
            "Is it a one-time sound or does it repeat continuously?",
        ],
    },
    "overheating": {
        "keywords": ["overheat", "temperature", "steam", "hot engine", "coolant"],
        "questions": [
            "Does the temperature gauge climb during city driving, highway driving, or both?",
            "Have you noticed any coolant leaking under the car or a sweet smell?",
            "When did you last top up or change the coolant?",
        ],
    },
    "brakes": {
        "keywords": ["brake", "brakes", "stopping"],
        "questions": [
            "Do you feel squealing, grinding, or a soft/spongy pedal when braking?",
            "Does the car pull to one side when you brake?",
            "When were the brake pads last checked or replaced?",
        ],
    },
    "ac": {
        "keywords": ["ac", "air conditioner", "cooling", "not cooling"],
        "questions": [
            "Is the AC blowing warm air, weak air, or no air at all?",
            "Do you hear any unusual noise when the AC compressor kicks in?",
            "When was the AC last serviced or gas refilled?",
        ],
    },
    "warning_light": {
        "keywords": ["check engine", "warning light", "dashboard light", "indicator"],
        "questions": [
            "Which warning light is on — check engine, battery, oil, or something else?",
            "Is the light steady or blinking?",
            "Has the car's performance changed since the light came on (power loss, rough idle, etc.)?",
        ],
    },
}

BOOKING_TRIGGER_WORDS = ["book", "yes", "schedule", "confirm", "sure", "ok", "okay", "please book"]


def is_car_related(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(kw in lowered for kw in CAR_KEYWORDS)


def is_greeting(text: str) -> bool:
    lowered = text.lower().strip()
    return any(lowered == g or lowered.startswith(g) for g in GREETING_WORDS)


def detect_symptom_category(text: str):
    lowered = text.lower()
    for category, data in SYMPTOM_TREES.items():
        if any(kw in lowered for kw in data["keywords"]):
            return category
    return None


def next_followup_question(category: str, asked_count: int):
    """Return the next rule-based follow-up question, or None if exhausted."""
    tree = SYMPTOM_TREES.get(category)
    if not tree:
        return None
    questions = tree["questions"]
    if asked_count < len(questions):
        return questions[asked_count]
    return None


def wants_booking(text: str) -> bool:
    lowered = text.lower().strip()
    return any(w in lowered for w in BOOKING_TRIGGER_WORDS)
