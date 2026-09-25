from django.contrib import admin
from .models import Conversation, Message, MediaUpload, Diagnosis, Booking

admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(MediaUpload)
admin.site.register(Diagnosis)
admin.site.register(Booking)
