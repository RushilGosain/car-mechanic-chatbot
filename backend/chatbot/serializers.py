from rest_framework import serializers
from .models import Conversation, Message, MediaUpload, Diagnosis, Booking


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "sender", "text", "media", "created_at"]


class MediaUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaUpload
        fields = ["id", "conversation", "file", "media_type", "analysis_note", "uploaded_at"]
        read_only_fields = ["analysis_note"]


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = [
            "id", "conversation", "summary", "probable_causes",
            "suggested_repair", "confidence", "used_ai", "created_at",
        ]


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id", "conversation", "diagnosis", "customer_name", "phone_number",
            "preferred_date", "notes", "status", "created_at",
        ]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "status", "vehicle_info", "created_at", "updated_at", "messages"]
