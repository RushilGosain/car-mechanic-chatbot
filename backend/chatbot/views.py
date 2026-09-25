from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from django.shortcuts import get_object_or_404

from .models import Conversation, Message, MediaUpload, Diagnosis, Booking
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    MediaUploadSerializer,
    DiagnosisSerializer,
    BookingSerializer,
)
from . import rules
from . import gemini_service


class ChatView(APIView):
    """
    POST /api/chat/

    Accepted body examples:

    {
        "message": "My car is making a strange noise"
    }

    or:

    {
        "message": {
            "content": "My car is making a strange noise"
        }
    }

    or:

    {
        "message": {
            "text": "My car is making a strange noise"
        }
    }

    conversation_id is optional.
    """

    def post(self, request):
        raw_message = request.data.get("message")
        conversation_id = request.data.get("conversation_id")

        # ---------------------------------------------------------
        # Normalize the message coming from the frontend
        # ---------------------------------------------------------
        if isinstance(raw_message, str):
            text = raw_message.strip()

        elif isinstance(raw_message, dict):
            # Support common frontend message formats.
            text = (
                raw_message.get("content")
                or raw_message.get("text")
                or raw_message.get("message")
                or ""
            )

            # Make sure the final value is a string.
            if not isinstance(text, str):
                text = str(text)

            text = text.strip()

        elif raw_message is None:
            text = ""

        else:
            text = str(raw_message).strip()

        # ---------------------------------------------------------
        # Get or create conversation
        # ---------------------------------------------------------
        if conversation_id:
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id
            )
        else:
            conversation = Conversation.objects.create()

        # ---------------------------------------------------------
        # Save user's message
        # ---------------------------------------------------------
        if text:
            Message.objects.create(
                conversation=conversation,
                sender="user",
                text=text,
            )

        ready_for_diagnosis = False

        # ---------------------------------------------------------
        # Rule-based conversation flow
        # ---------------------------------------------------------
        if not text:
            bot_reply = (
                "Could you describe the issue you're experiencing "
                "with your car?"
            )

        elif rules.is_greeting(text) and not conversation.current_category:
            bot_reply = rules.GREETING_REPLY

        elif (
            not rules.is_car_related(text)
            and not conversation.current_category
        ):
            bot_reply = rules.OFF_TOPIC_REPLY

        else:
            # Detect symptom category if we don't already have one.
            if not conversation.current_category:
                category = rules.detect_symptom_category(text)

                if category:
                    conversation.current_category = category
                    conversation.followups_asked = 0

                else:
                    bot_reply = (
                        "Got it. Can you tell me a bit more — is it a "
                        "noise, a warning light, trouble starting, "
                        "overheating, braking, or an AC issue?"
                    )

                    Message.objects.create(
                        conversation=conversation,
                        sender="bot",
                        text=bot_reply,
                    )

                    conversation.save()

                    return Response({
                        "conversation_id": conversation.id,
                        "bot_reply": bot_reply,
                        "ready_for_diagnosis": False,
                    })

            # Ask the next rule-based follow-up question.
            question = rules.next_followup_question(
                conversation.current_category,
                conversation.followups_asked,
            )

            if question:
                bot_reply = question
                conversation.followups_asked += 1

            else:
                bot_reply = (
                    "Thanks, that's enough detail for me to work with. "
                    "Shall I go ahead and put together a diagnosis? "
                    "(You can also upload a photo, audio, or video first "
                    "if that helps.)"
                )

                ready_for_diagnosis = True

        # ---------------------------------------------------------
        # Save conversation
        # ---------------------------------------------------------
        conversation.save()

        # Save bot response.
        Message.objects.create(
            conversation=conversation,
            sender="bot",
            text=bot_reply,
        )

        return Response({
            "conversation_id": conversation.id,
            "bot_reply": bot_reply,
            "ready_for_diagnosis": ready_for_diagnosis,
        })


class UploadView(APIView):
    """
    POST /api/upload/

    multipart/form-data:
        conversation_id
        media_type (image/audio/video)
        file
    """

    def post(self, request):
        conversation_id = request.data.get("conversation_id")
        media_type = request.data.get("media_type")
        file_obj = request.FILES.get("file")

        if not (conversation_id and media_type and file_obj):
            return Response(
                {
                    "error": (
                        "conversation_id, media_type and file "
                        "are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
        )

        media = MediaUpload.objects.create(
            conversation=conversation,
            file=file_obj,
            media_type=media_type,
        )

        # AI is used only for images.
        if media_type == "image":
            media.analysis_note = gemini_service.analyze_image(
                media.file.path
            )
        else:
            media.analysis_note = (
                f"{media_type.capitalize()} file received and "
                "attached to the conversation for technician review."
            )

        media.save()

        Message.objects.create(
            conversation=conversation,
            sender="user",
            text=f"[Uploaded {media_type}] {media.analysis_note}",
            media=media,
        )

        return Response(
            MediaUploadSerializer(media).data,
            status=status.HTTP_201_CREATED,
        )


class DiagnosisView(APIView):
    """
    POST /api/diagnosis/

    body:
    {
        "conversation_id": "<uuid>"
    }

    This is the ONE point in the app that calls Gemini for reasoning.
    """

    def post(self, request):
        conversation_id = request.data.get("conversation_id")

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
        )

        transcript = "\n".join(
            f"{m.sender.upper()}: {m.text}"
            for m in conversation.messages.all()
            if m.text
        )

        media_notes = "\n".join(
            f"- {m.media_type}: {m.analysis_note}"
            for m in conversation.media_uploads.all()
            if m.analysis_note
        )

        result = gemini_service.generate_diagnosis(
            transcript,
            media_notes,
        )

        diagnosis = Diagnosis.objects.create(
            conversation=conversation,
            **result,
        )

        conversation.status = "diagnosed"
        conversation.save()

        bot_text = (
            f"Diagnosis: {diagnosis.summary}\n\n"
            f"Recommended action: {diagnosis.suggested_repair}\n\n"
            "Would you like me to book a mechanic for this?"
        )

        Message.objects.create(
            conversation=conversation,
            sender="bot",
            text=bot_text,
        )

        data = DiagnosisSerializer(diagnosis).data
        data["book_recommended"] = True

        return Response(
            data,
            status=status.HTTP_201_CREATED,
        )


class BookingView(APIView):
    """
    POST /api/booking/

    body:
    {
        "conversation_id": "...",
        "customer_name": "...",
        "phone_number": "...",
        "preferred_date": "...",
        "notes": "..."
    }
    """

    def post(self, request):
        conversation_id = request.data.get("conversation_id")

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
        )

        latest_diagnosis = (
            conversation.diagnoses
            .order_by("-created_at")
            .first()
        )

        serializer = BookingSerializer(
            data={
                "conversation": conversation.id,
                "diagnosis": (
                    latest_diagnosis.id
                    if latest_diagnosis
                    else None
                ),
                "customer_name": request.data.get(
                    "customer_name",
                    "",
                ),
                "phone_number": request.data.get(
                    "phone_number",
                    "",
                ),
                "preferred_date": request.data.get(
                    "preferred_date"
                ),
                "notes": request.data.get(
                    "notes",
                    "",
                ),
                "status": "pending",
            }
        )

        serializer.is_valid(raise_exception=True)

        booking = serializer.save()

        conversation.status = "booked"
        conversation.save()

        Message.objects.create(
            conversation=conversation,
            sender="bot",
            text=(
                f"Booking confirmed (ID #{booking.id}). "
                "A mechanic will contact you shortly."
            ),
        )

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )


class BookingDetailView(RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class ConversationDetailView(RetrieveAPIView):
    """
    GET /api/conversation/<id>/
    """

    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer