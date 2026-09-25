"""
Gemini service for the Car Mechanic Chatbot.

Gemini is used only where AI adds real value:
1. Generating the final diagnosis from the conversation.
2. Analyzing uploaded vehicle images.

The normal chat flow remains rule-based in rules.py.

If a Gemini model is temporarily unavailable, the service
automatically tries another supported Gemini model before
falling back to the deterministic diagnosis.
"""

import time

from django.conf import settings


# Try models in this order.
#
# If one model is temporarily unavailable, the next
# model will automatically be attempted.
DIAGNOSIS_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]


# Models used for image analysis.
IMAGE_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]


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
    or if the Google GenAI SDK is unavailable.
    """

    if not settings.GEMINI_API_KEY:
        print("Gemini client: API key is missing.")
        return None

    try:
        from google import genai
    except ImportError:
        print(
            "Gemini client: google-genai package "
            "is not installed."
        )
        return None

    try:
        client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        print(
            "Gemini client: initialized successfully."
        )

        return client

    except Exception as exc:
        print(
            "========== GEMINI CLIENT ERROR =========="
        )
        print(type(exc).__name__)
        print(str(exc))
        print(
            "========================================="
        )

        return None


def _is_temporary_error(exc):
    """
    Determine whether a Gemini error is temporary
    and worth retrying.
    """

    error_message = str(exc).lower()

    return (
        "503" in error_message
        or "unavailable" in error_message
        or "high demand" in error_message
        or "429" in error_message
        or "resource exhausted" in error_message
        or "rate limit" in error_message
    )


def generate_diagnosis(
    conversation_text: str,
    media_notes: str = "",
):
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

    If one Gemini model is temporarily unavailable,
    another model is attempted.

    If all Gemini models fail, a deterministic
    fallback diagnosis is returned.
    """

    client = _get_client()

    if client is None:
        return _fallback_diagnosis(
            conversation_text
        )

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Conversation:\n{conversation_text}\n\n"
        f"Media notes:\n{media_notes or 'None'}"
    )

    print(
        "Sending diagnosis request to Gemini..."
    )

    # Try each model.
    for model_index, model_name in enumerate(
        DIAGNOSIS_MODELS
    ):

        print(
            f"Trying Gemini model "
            f"{model_index + 1}/"
            f"{len(DIAGNOSIS_MODELS)}: "
            f"{model_name}"
        )

        # Try each model twice for temporary errors.
        for attempt in range(1, 3):

            try:

                print(
                    f"Attempt {attempt}/2 "
                    f"using {model_name}..."
                )

                response = (
                    client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                )

                response_text = (
                    response.text or ""
                ).strip()

                print(
                    f"Gemini response received "
                    f"from {model_name}."
                )

                if not response_text:

                    print(
                        "Gemini returned an empty "
                        "response."
                    )

                    return _fallback_diagnosis(
                        conversation_text
                    )

                print(
                    "Gemini raw response:"
                )
                print(response_text)

                # IMPORTANT:
                # Only return fields that actually exist
                # in the Django Diagnosis model.
                return _parse_diagnosis_response(
                    response_text
                )

            except Exception as exc:

                print(
                    "========== GEMINI API ERROR =========="
                )
                print(
                    f"Model: {model_name}"
                )
                print(
                    f"Attempt: {attempt}/2"
                )
                print(
                    f"Error type: "
                    f"{type(exc).__name__}"
                )
                print(
                    f"Error: {str(exc)}"
                )
                print(
                    "======================================"
                )

                # Do not retry authentication,
                # invalid-request, or other permanent errors.
                if not _is_temporary_error(exc):

                    print(
                        "Non-retryable Gemini "
                        "error. Stopping."
                    )

                    return _fallback_diagnosis(
                        conversation_text
                    )

                # Retry the same model once.
                if attempt == 1:

                    print(
                        "Temporary Gemini error."
                    )

                    print(
                        "Retrying same model "
                        "in 2 seconds..."
                    )

                    time.sleep(2)

                    continue

                # Both attempts failed.
                print(
                    f"{model_name} is currently "
                    f"unavailable."
                )

                print(
                    "Moving to the next Gemini model..."
                )

                break

    # Every model failed.
    print(
        "All Gemini models are currently "
        "unavailable."
    )

    print(
        "Using deterministic fallback diagnosis."
    )

    return _fallback_diagnosis(
        conversation_text
    )


def _parse_diagnosis_response(text: str):
    """
    Convert Gemini's structured response into the
    dictionary expected by the Django API.

    IMPORTANT:
    Do not add extra keys here unless the corresponding
    fields exist in the Diagnosis Django model.
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

            if stripped_line.upper().startswith(
                prefix
            ):

                fields[key] = (
                    stripped_line
                    .split(":", 1)[1]
                    .strip()
                )

    causes = fields["CAUSES"]

    if " | " in causes:

        causes = causes.replace(
            " | ",
            "\n"
        )

    confidence = (
        fields["CONFIDENCE"]
        or "medium"
    ).lower()

    # Make sure confidence matches the expected
    # values used by the application.
    if confidence not in {
        "low",
        "medium",
        "high",
    }:

        confidence = "medium"

    return {
        "summary": (
            fields["SUMMARY"]
            or (
                "The technician reviewed the "
                "conversation but could not form "
                "a clear summary."
            )
        ),

        "probable_causes": (
            causes
            or "Insufficient information provided."
        ),

        "suggested_repair": (
            fields["REPAIR"]
            or (
                "Please visit a service center "
                "for a physical inspection."
            )
        ),

        "confidence": confidence,

        "used_ai": True,
    }


def _fallback_diagnosis(
    conversation_text: str,
):
    """
    Deterministic fallback used when Gemini is unavailable.
    """

    return {
        "summary": (
            "Based on the symptoms you described, "
            "this looks like it needs a closer physical "
            "inspection to pinpoint the exact cause. "
            "Common issues matching this pattern involve "
            "wear parts or fluid levels."
        ),

        "probable_causes": (
            "Worn component\n"
            "Low or degraded fluid\n"
            "Loose or damaged connection"
        ),

        "suggested_repair": (
            "Book a diagnostic inspection with a "
            "mechanic so the exact part can be "
            "identified and replaced."
        ),

        "confidence": "low",

        "used_ai": False,
    }


def analyze_image(file_path: str) -> str:
    """
    Analyze an uploaded vehicle image using Gemini.
    """

    client = _get_client()

    if client is None:

        return (
            "Image received. AI visual analysis is "
            "unavailable without a configured Gemini "
            "API key; the technician will review it "
            "after diagnosis."
        )

    try:

        uploaded_file = client.files.upload(
            file=file_path
        )

        print(
            "Vehicle image uploaded to Gemini."
        )

    except Exception as exc:

        print(
            "========== GEMINI FILE ERROR =========="
        )
        print(type(exc).__name__)
        print(str(exc))
        print(
            "========================================"
        )

        return (
            "Image received but could not be "
            "uploaded for automatic analysis. "
            "The technician will review it manually."
        )

    for model_name in IMAGE_MODELS:

        try:

            print(
                f"Trying image analysis with "
                f"{model_name}..."
            )

            response = (
                client.models.generate_content(
                    model=model_name,
                    contents=[
                        uploaded_file,
                        (
                            "You are a car mechanic. "
                            "In 2 short sentences, "
                            "describe any visible issue "
                            "in this image relevant to "
                            "vehicle diagnosis, such as "
                            "rust, leaks, damage, warning "
                            "lights, worn parts, smoke, "
                            "or other visible vehicle "
                            "problems."
                        ),
                    ],
                )
            )

            response_text = (
                response.text or ""
            ).strip()

            if response_text:

                print(
                    f"Gemini image analysis "
                    f"successful using {model_name}."
                )

                return response_text

            print(
                f"{model_name} returned an empty "
                "image response."
            )

        except Exception as exc:

            print(
                "========== GEMINI IMAGE ERROR =========="
            )
            print(
                f"Model: {model_name}"
            )
            print(
                f"Error type: "
                f"{type(exc).__name__}"
            )
            print(
                f"Error: {str(exc)}"
            )
            print(
                "========================================="
            )

            if _is_temporary_error(exc):

                print(
                    "Trying next image model..."
                )

                continue

            break

    return (
        "Image received but Gemini could not "
        "analyze it at the moment. The technician "
        "will review it manually."
    )