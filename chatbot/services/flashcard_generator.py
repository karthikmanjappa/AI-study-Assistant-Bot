# chatbot/services/flashcard_generator.py

import json
import os
from openai import OpenAI

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY")
)


def generate_flashcards_from_text(text: str, topic: str = "") -> list:
    """
    Uses OpenRouter (same as qa_engine) to generate flashcards from text.
    Returns list of {"question": "...", "answer": "..."} dicts.
    """

    prompt = f"""You are a study assistant. Given the following educational text, generate 5 flashcards.
Each flashcard must have a clear question and a concise answer.

Text:
{text[:3000]}

Return ONLY a valid JSON array like this (no explanation, no markdown, no backticks):
[
    {{"question": "What is X?", "answer": "X is ..."}},
    {{"question": "What is Y?", "answer": "Y is ..."}}
]"""

    response = openrouter_client.chat.completions.create(
        model="openrouter/owl-alpha",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if "```" in raw:
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    # Find JSON array start and end
    start = raw.find("[")
    end = raw.rfind("]") + 1

    if start == -1 or end == 0:
        raise Exception(f"No valid JSON array in response: {raw[:200]}")

    cards = json.loads(raw[start:end])
    return cards


def save_flashcards(user, flashcards: list, topic: str = ""):
    from chatbot.models import Flashcard
    saved = []
    for card in flashcards:
        fc = Flashcard.objects.create(
            user=user,
            question=card.get("question", ""),
            answer=card.get("answer", ""),
            topic=topic,
        )
        saved.append(fc)
    return saved