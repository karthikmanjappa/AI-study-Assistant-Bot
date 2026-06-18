# chatbot/admin.py
from django.contrib import admin
from .models import (
    Document, ChatHistory,
    StudyStreak, StudySession,
    TopicStat, Flashcard
)

admin.site.register(Document)
admin.site.register(ChatHistory)
admin.site.register(StudyStreak)
admin.site.register(StudySession)
admin.site.register(TopicStat)
admin.site.register(Flashcard)
