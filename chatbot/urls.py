from django.urls import path
from . import views
from .views import firebase_login 
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Main Chat Page
    path('', views.chat_view, name='chat'),

    # Chat API
    path('ask/', views.ask_question, name='ask'),

    # PDF Upload
    path('upload/', views.upload_pdf, name='upload_pdf'),

    #History Management
    path('history/clear/', views.clear_history, name='clear_history'),


    # Extra Features
    path('summarize/', views.summarize_view, name='summarize'),
    path('quiz/', views.quiz_view, name='quiz'),

    path('history/', views.get_history, name='history'),
    path('history/delete/<int:id>/', views.delete_history, name='delete_history'),

    #transcription
    path('transcribe/', views.transcribe_view, name='transcribe'),

    #firebase auth
    path('firebase-login/', views.firebase_login, name='firebase_login'),

   # ── NEW ──────────────────────────────────
    path('flashcards/', views.my_flashcards, name='flashcards'),
    path('flashcards/generate/', views.generate_flashcards, name='generate_flashcards'),
    path('flashcards/<int:pk>/mark/', views.mark_flashcard, name='mark_flashcard'),

    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('analytics/api/', views.analytics_api, name='analytics_api'),


]