"""
Gemini service for the Car Mechanic Chatbot.

Gemini is used only where AI adds real value:
1. Generating the final diagnosis from the conversation.
2. Analyzing uploaded vehicle images.

The normal chat flow remains rule-based in rules.py.
If Gemini is unavailable, the application falls back to a
deterministic diagnosis instead of crashing.
"""

from django.conf import settings


MODEL_NAME = "gemini-3.8-flash"


SYSTEM_PROMPT = (
    "You are a senior automobile technician with 20 years of experience. "
    "A car owner has described symptoms through a chat. "
    "Based on the conversation, provide a concise and practical diagnosis. "
    "Do not invent information that was not provided. "
    "Respond in exactly this format with no extra commentary:\n"
    "SUMMARY: <one paragraph plain-language summary of the likely problem>\n"
    "CAUSES: <up to 3 probable causes, separated by ' | '>\n"
    "REPAIR: <the recommended repair or service action>\n"
    "CONFIDENCE: <low, medium, or high>"
)


def _get_client():
    """
    Create and return the Google GenAI client.

    Returns None if the Gemini API key is not configured
    or if the new Google GenAI SDK is unavailable.
    """

    if not settings.GEMINI_API_KEY:
        print("Gemini client: API key is missing.")
        return None

    try:
        from google import genai
    except ImportError:
        print("Gemini client: google-genai package is not installed.")
        return None

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        print("Gemini client: initialized successfully.")
        return client
    except Exception as exc:
        print("Gemini client initialization failed:")
        print(type(exc).__name__)
        print(str(exc))
        return None


def generate_diagnosis(conversation_text: str, media_notes: str = ""):
    """
    Generate a diagnosis using Gemini.

    Returns:

    {
        "summary": str,
        "probable_causes": str,
        "suggested_repair": str,
        "confidence": str,
        "used_ai": bool
    }

    If Gemini is unavailable or the request fails, a deterministic
    fallback response is returned.
    """

    client = _get_client()

    if client is None:
        return _fallback_diagnosis(conversation_text)

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Conversation:\n{conversation_text}\n\n"
        f"Media notes:\n{media_notes or 'None'}"
    )

    print("Sending diagnosis request to Gemini...")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        response_text = (response.text or "").strip()

        print("Gemini response received successfully.")

        if not response_text:
            print("Gemini returned an empty response.")
            return _fallback_diagnosis(conversation_text)

        return _parse_diagnosis_response(response_text)

    except Exception as exc:
        print("========== GEMINI API ERROR ==========")
        print(type(exc).__name__)
        print(str(exc))
        print("======================================")

        return _fallback_diagnosis(conversation_text)


def _parse_diagnosis_response(text: str):
    """
    Convert Gemini's structured text response into the dictionary
    expected by the Django API.
    """

    fields = {
        "SUMMARY": "",
        "CAUSES": "",
        "REPAIR": "",
        "CONFIDENCE": "medium",
    }

    for line in text.strip().splitlines():
        stripped_line = line.strip()

        for key in fields:
            prefix = f"{key}:"

            if stripped_line.upper().startswith(prefix):
                fields[key] = stripped_line.split(":", 1)[1].strip()

    causes = fields["CAUSES"]

    if " | " in causes:
        causes = causes.replace(" | ", "\n")

    return {
        "summary": (
            fields["SUMMARY"]
            or "The technician reviewed the conversation but could not form a clear summary."
        ),
        "probable_causes": (
            causes
            or "Insufficient information provided."
        ),
        "suggested_repair": (
            fields["REPAIR"]
            or "Please visit a service center for a physical inspection."
        ),
        "confidence": (
            fields["CONFIDENCE"] or "medium"
        ).lower(),
        "used_ai": True,
    }


def _fallback_diagnosis(conversation_text: str):
    """
    Deterministic diagnosis used when Gemini is unavailable.

    This ensures the application still works even when:
    - API key is missing
    - API request fails
    - Gemini quota is unavailable
    - network/API error occurs
    """

    return {
        "summary": (
            "Based on the symptoms you described, this looks like it needs "
            "a closer physical inspection to pinpoint the exact cause. "
            "Common issues matching this pattern involve wear parts or "
            "fluid levels."
        ),
        "probable_causes": (
            "Worn component\n"
            "Low or degraded fluid\n"
            "Loose or damaged connection"
        ),
        "suggested_repair": (
            "Book a diagnostic inspection with a mechanic so the exact "
            "part can be identified and replaced."
        ),
        "confidence": "low",
        "used_ai": False,
    }


def analyze_image(file_path: str) -> str:
    """
    Analyze an uploaded vehicle image using Gemini vision.
    """

    client = _get_client()

    if client is None:
        return (
            "Image received. AI visual analysis is unavailable without "
            "a configured Gemini API key; the technician will review it "
            "after diagnosis."
        )

    try:
        from google import genai

        uploaded_file = client.files.upload(file=file_path)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                uploaded_file,
                (
                    "You are a car mechanic. In 2 short sentences, "
                    "describe any visible issue in this image relevant "
                    "to vehicle diagnosis, such as rust, leaks, damage, "
                    "warning lights, worn parts, smoke, or other visible "
                    "vehicle problems."
                ),
            ],
        )

        response_text = (response.text or "").strip()

        if response_text:
            return response_text

        return (
            "Image was uploaded successfully, but Gemini did not "
            "return a visual analysis."
        )

    except Exception as exc:
        print("========== GEMINI IMAGE ERROR ==========")
        print(type(exc).__name__)
        print(str(exc))
        print("=========================================")

        return (
            "Image received but could not be analyzed automatically. "
            "The technician will review it manually."
        )