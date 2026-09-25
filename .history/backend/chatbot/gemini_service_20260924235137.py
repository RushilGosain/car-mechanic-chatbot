"""
Thin wrapper around the Gemini free API.

Design intent (per task brief): AI is used ONLY where it genuinely adds
value — synthesizing a diagnosis from a free-form conversation, and
reading an uploaded image. Everything else (topic filtering, follow-up
question flow, booking) is handled by plain Python logic in rules.py.

If GEMINI_API_KEY is not configured, this module degrades gracefully to
a rule-based fallback so the rest of the app still works end-to-end.
"""
from django.conf import settings

SYSTEM_PROMPT = (
    "You are a senior automobile technician with 20 years of experience. "
    "A car owner has described symptoms through a chat. Based on the "
    "conversation below, give a concise diagnosis. Respond in this exact "
    "format with no extra commentary:\n"
    "SUMMARY: <one paragraph plain-language summary of the likely problem>\n"
    "CAUSES: <up to 3 probable causes, separated by ' | '>\n"
    "REPAIR: <the recommended repair/service action>\n"
    "CONFIDENCE: <low, medium, or high>"
)


def _get_model():
    # Imported lazily and only when a key is actually configured: importing
    # this SDK eagerly triggers background credential-discovery network calls
    # even when it's never used, which slows down / can hang a keyless setup.
    if not settings.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
    except ImportError:
        return None
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-1.5-flash")


def generate_diagnosis(conversation_text: str, media_notes: str = ""):
    """
    Returns a dict: {summary, probable_causes, suggested_repair, confidence, used_ai}
    Falls back to a deterministic rule-based response if no API key is set.
    """
    model = _get_model()
    if model is None:
        return _fallback_diagnosis(conversation_text)

    prompt = f"{SYSTEM_PROMPT}\n\nConversation:\n{conversation_text}\n\nMedia notes:\n{media_notes or 'None'}"
    try:
        response = model.generate_content(prompt)
        return _parse_diagnosis_response(response.text)
    except Exception as e:
    return("========== GEMINI ERROR ==========")
    print(type(e).__name__)
    print(str(e))
    print("==================================")
    return _fallback_diagnosis(conversation_text)


def _parse_diagnosis_response(text: str):
    fields = {"SUMMARY": "", "CAUSES": "", "REPAIR": "", "CONFIDENCE": "medium"}
    for line in text.strip().splitlines():
        for key in fields:
            prefix = f"{key}:"
            if line.strip().upper().startswith(prefix):
                fields[key] = line.split(":", 1)[1].strip()
    return {
        "summary": fields["SUMMARY"] or "The technician reviewed the conversation but could not form a clear summary.",
        "probable_causes": fields["CAUSES"].replace(" | ", "\n") or "Insufficient information provided.",
        "suggested_repair": fields["REPAIR"] or "Please visit a service center for a physical inspection.",
        "confidence": (fields["CONFIDENCE"] or "medium").lower(),
        "used_ai": True,
    }


def _fallback_diagnosis(conversation_text: str):
    """Deterministic, non-AI diagnosis used when Gemini is unavailable."""
    return {
        "summary": (
            "Based on the symptoms you described, this looks like it needs a closer "
            "physical inspection to pinpoint the exact cause. Common issues matching "
            "this pattern involve wear parts or fluid levels."
        ),
        "probable_causes": "Worn component\nLow or degraded fluid\nLoose or damaged connection",
        "suggested_repair": "Book a diagnostic inspection with a mechanic so the exact part can be identified and replaced.",
        "confidence": "low",
        "used_ai": False,
    }


def analyze_image(file_path: str) -> str:
    """Lightweight image analysis using Gemini vision, only for uploaded images."""
    model = _get_model()
    if model is None:
        return "Image received. AI visual analysis is unavailable without a configured Gemini API key; the technician will review it after diagnosis."
    try:
        import google.generativeai as genai
        uploaded = genai.upload_file(file_path)
        response = model.generate_content([
            uploaded,
            "You are a car mechanic. In 2 short sentences, describe any visible "
            "issue in this image relevant to vehicle diagnosis (rust, leak, "
            "damage, warning light, worn part, etc).",
        ])
        return response.text.strip()
    except Exception:
        return "Image received but could not be analyzed automatically. The technician will review it manually."
