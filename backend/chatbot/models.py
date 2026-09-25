import uuid
from django.db import models


class Conversation(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("diagnosed", "Diagnosed"),
        ("booked", "Booked"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    vehicle_info = models.CharField(max_length=255, blank=True, default="")
    current_category = models.CharField(max_length=30, blank=True, default="")
    followups_asked = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} ({self.status})"


class MediaUpload(models.Model):
    MEDIA_TYPES = [("image", "Image"), ("audio", "Audio"), ("video", "Video")]

    conversation = models.ForeignKey(Conversation, related_name="media_uploads", on_delete=models.CASCADE)
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    analysis_note = models.TextField(blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.media_type} upload for {self.conversation_id}"


class Message(models.Model):
    SENDER_CHOICES = [("user", "User"), ("bot", "Bot")]

    conversation = models.ForeignKey(Conversation, related_name="messages", on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField(blank=True, default="")
    media = models.ForeignKey(MediaUpload, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.sender}] {self.text[:40]}"


class Diagnosis(models.Model):
    conversation = models.ForeignKey(Conversation, related_name="diagnoses", on_delete=models.CASCADE)
    summary = models.TextField()
    probable_causes = models.TextField(help_text="Newline-separated list of probable causes")
    suggested_repair = models.TextField()
    confidence = models.CharField(max_length=20, default="medium")
    used_ai = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis for {self.conversation_id} @ {self.created_at:%Y-%m-%d %H:%M}"


class Booking(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")]

    conversation = models.ForeignKey(Conversation, related_name="bookings", on_delete=models.CASCADE)
    diagnosis = models.ForeignKey(Diagnosis, null=True, blank=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=20)
    preferred_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} for {self.customer_name} ({self.status})"
