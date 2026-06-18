# chatbot/services/analytics.py

from django.utils import timezone
from django.db.models import Count


def get_or_create_streak(user):
    from chatbot.models import StudyStreak
    streak, _ = StudyStreak.objects.get_or_create(user=user)
    return streak


def record_study_activity(user=None, topic: str = "", subject: str = ""):
    from chatbot.models import StudySession, TopicStat, StudyStreak

    # 1. Update streak (only if user exists)
    if user:
        streak = get_or_create_streak(user)
        streak.update_streak()

    # 2. Create session (works without user too)
    session = StudySession.objects.create(
        user=user,
        topic=topic[:255] if topic else "General",
        subject=subject,
    )

    # 3. Update topic stats (only if user exists)
    if user and topic:
        stat, created = TopicStat.objects.get_or_create(
            user=user,
            topic=topic[:255]
        )
        if not created:
            stat.study_count += 1
            stat.save()

    return session


def get_analytics_data(user=None):
    from chatbot.models import StudyStreak, StudySession, TopicStat

    # Last 7 days activity (works without user)
    seven_days_ago = timezone.now() - timezone.timedelta(days=7)

    if user:
        streak = get_or_create_streak(user)
        daily_activity = (
            StudySession.objects
            .filter(user=user, started_at__gte=seven_days_ago)
            .extra(select={"day": "date(started_at)"})
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        top_topics = (
            TopicStat.objects
            .filter(user=user)
            .order_by("-study_count")[:5]
            .values("topic", "study_count")
        )
        current_streak = streak.current_streak
        longest_streak = streak.longest_streak
        total_study_days = streak.total_study_days
    else:
        # No user — show global stats
        daily_activity = (
            StudySession.objects
            .filter(started_at__gte=seven_days_ago)
            .extra(select={"day": "date(started_at)"})
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        top_topics = (
            StudySession.objects
            .filter(topic__isnull=False)
            .values("topic")
            .annotate(study_count=Count("id"))
            .order_by("-study_count")[:5]
        )
        current_streak = 0
        longest_streak = 0
        total_study_days = StudySession.objects.count()

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_study_days": total_study_days,
        "daily_activity": list(daily_activity),
        "top_topics": list(top_topics),
    }