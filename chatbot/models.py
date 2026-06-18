# chatbot/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Document(models.Model):
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name}"


class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.question[:50]}"

    class Meta:
        ordering = ['-created_at']


class StudyStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)
    total_study_days = models.IntegerField(default=0)

    def update_streak(self):
        today = timezone.now().date()
        if self.last_study_date == today:
            return
        elif self.last_study_date == today - timezone.timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1
        self.last_study_date = today
        self.total_study_days += 1
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.save()

    def __str__(self):
        return f"{self.user.username} - streak: {self.current_streak}"


class StudySession(models.Model):
    user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    topic = models.CharField(max_length=255)
    subject = models.CharField(max_length=100, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    duration_minutes = models.IntegerField(default=0)
    messages_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.topic}"

    class Meta:
        ordering = ['-started_at']


class TopicStat(models.Model):
    user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    topic = models.CharField(max_length=255)
    study_count = models.IntegerField(default=1)
    last_studied = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'topic')
        ordering = ['-study_count']

    def __str__(self):
        return f"{self.user.username} - {self.topic} x{self.study_count}"


class Flashcard(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()
    topic = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    times_reviewed = models.IntegerField(default=0)
    last_reviewed = models.DateTimeField(null=True, blank=True)
    is_mastered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.topic} - {self.question[:50]}"

    class Meta:
        ordering = ['-created_at']