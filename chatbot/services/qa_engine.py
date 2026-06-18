import base64
import os
from google import genai
from google.genai import types
from openai import OpenAI
from .embeddings import model
from .vector_store import search

# Paste your Gemini API key directly here (overrides any system env vars)

GEMINI_API_KEY = "AQ.Ab8RN6ILHKo1L1dvrWFCtJgaGpd-s3NQrTJY3uxvuFtrAHM6vw"

# ✅ Separate names for each client
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY")
)

# ✅ Updated FREE_MODELS - verified June 2026
MODELS_TO_TEST = [
    "openrouter/owl-alpha",
    "openai/gpt-oss-120b:free",
    "openai/gpt-oss-20b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-31b-it:free",
    "z-ai/glm-4.5-air:free",
    "moonshotai/kimi-k2.6:free",
    "deepseek/deepseek-r1:free",
    "nvidia/nemotron-nano-9b-v2:free",
]

SYSTEM_INSTRUCTION = """You are an expert AI assistant with accurate knowledge in:
- All Indian languages and their literature (Hindi, Kannada, Tamil, Telugu, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, Urdu, Sanskrit, and more).
- Literature of all kinds: poetry, novels, short stories, essays, dramas, biographies.
- History: ancient, medieval, modern — Indian and world history.
- Films: Indian cinema (Bollywood, Tollywood, Kollywood, Sandalwood, etc.) and world cinema.
- General knowledge: science, geography, culture, current affairs.
- All programming languages: Python, Java, C, C++, JavaScript, SQL, and more.
- Image Detection and analysis: you can analyze images and provide detailed descriptions, identify objects, and answer questions about the content of images.
- Current affairs: you are aware of recent events and developments in india and around the world, including politics, economics, science, and technology.

Rules:
1. Give ACCURATE and DETAILED information only
2. Reply in the SAME language the user writes in — if they write in Kannada, reply in Kannada; Hindi → Hindi; Tamil → Tamil; English → English
3. For authors/poets: include birth/death years, major works with descriptions, awards, and literary significance
4. For coding questions: provide correct, working code with clear explanation
5. For history: include accurate dates, key figures, and context
6. If unsure about something → say so honestly
7. Never hallucinate or invent facts"""


def get_answer(query, conversation_history=None):
    if conversation_history is None:
        conversation_history = []

    query_embedding = model.encode([query])[0]
    relevant_chunks = search(query_embedding)

    if relevant_chunks:
        context = " ".join(relevant_chunks)
        current_prompt = f"PDF Context:\n{context}\n\nQuestion: {query}"
    else:
        current_prompt = query

    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]

    for msg in conversation_history:
        messages.append({"role": msg.get("role"), "content": msg.get("content", "")})

    messages.append({"role": "user", "content": current_prompt})

    response = openrouter_client.chat.completions.create(
        model="openrouter/owl-alpha",           
        messages=messages,
        max_tokens=800,
    )

    answer = response.choices[0].message.content

    # Record study activity (no user since Firebase handles auth)
    try:
        from chatbot.services.analytics import record_study_activity
        record_study_activity(
            user=None,
            topic=query[:255],
            subject=""
        )
    except Exception:
        pass  # Never break chat if analytics fails

    return answer


def get_answer_with_image(query, image_data, mime_type="image/jpeg"):
    """
    query: the question/prompt about the image (string)
    image_data: either a base64-encoded string OR raw bytes
    mime_type: e.g. "image/jpeg", "image/png"
    """
    # Handle both base64 strings and raw bytes
    if isinstance(image_data, str):
        image_bytes = base64.b64decode(image_data)
    else:
        image_bytes = image_data

    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=mime_type
    )

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
        ),
        contents=[image_part, query]
    )

    return response.text