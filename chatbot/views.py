
from django.shortcuts import render
from django.http import JsonResponse
from .forms import UploadForm
from .models import ChatHistory
import json


from django.contrib.auth import login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .firebase_auth import verify_firebase_token

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.utils import timezone
import json

from chatbot.services.flashcard_generator import generate_flashcards_from_text, save_flashcards
from chatbot.services.analytics import record_study_activity, get_analytics_data
from chatbot.models import Flashcard

# ✅ MUST BE FIRST TWO LINES
import os
os.environ["PATH"] = r"D:\Downloads\ffmpeg\ffmpeg-master-latest-win64-gpl-shared\bin" + os.pathsep + os.environ.get("PATH", "")

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import UploadForm
from .models import ChatHistory
import tempfile
import whisper

# ✅ Load whisper model once
whisper_model = whisper.load_model("base")

# ... rest of your views below

# AI Services
from .services.qa_engine import get_answer, get_answer_with_image
from .services.pdf_utils import extract_text_from_pdf
from .services.embeddings import get_embeddings
from .services.vector_store import store_embeddings
from .services.summarizer import summarize_text
from .services.quiz_generator import generate_quiz



from django.middleware.csrf import get_token  # ← add this import at top

def chat_view(request):
    get_token(request)  # ← add this line
    if 'conversation_history' not in request.session:
        request.session['conversation_history'] = []
    return render(request, 'chatbot/chat.html')

@csrf_exempt
def clear_history(request):
    if request.method == "POST":
        ChatHistory.objects.all().delete()
        return JsonResponse({"message": "Cleared"})
    return JsonResponse({"message": "Invalid request"})


# ✅ Chat API with Memory
def ask_question(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get("question", "").strip()
            clear_memory = data.get("clear_memory", False)

            if not question:
                return JsonResponse({"answer": "Please ask a question."})

            # Clear memory if new chat
            if clear_memory:
                request.session['conversation_history'] = []
                request.session.modified = True
                return JsonResponse({"answer": "Memory cleared! Starting fresh conversation."})

            # Get conversation history from session
            conversation_history = request.session.get('conversation_history', [])

            # Get AI answer with memory
            answer = get_answer(question, conversation_history)

            # Update conversation history
            conversation_history.append({"role": "user", "content": question})
            conversation_history.append({"role": "assistant", "content": answer})

            # Keep only last 20 messages (10 exchanges) in session
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]

            request.session['conversation_history'] = conversation_history
            request.session.modified = True

            # Save to database
            ChatHistory.objects.create(
                question=question,
                answer=answer
            )

            return JsonResponse({"answer": answer})

        except Exception as e:
            return JsonResponse({"answer": f"Error: {str(e)}"})

    return JsonResponse({"answer": "Invalid request"})


# ✅ Clear Memory API
def clear_memory(request):
    if request.method == "POST":
        request.session['conversation_history'] = []
        request.session.modified = True
        return JsonResponse({"message": "Memory cleared ✅"})
    return JsonResponse({"message": "Invalid request"})


# ✅ Get History from DB

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  
def get_history(request):
    try:
        history = ChatHistory.objects.all().order_by('-created_at')[:20]
        data = [
            {
                "id": h.id,
                "question": h.question,
                "answer": h.answer,
                "created_at": h.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for h in history
        ]
        return JsonResponse({"history": data})
    except Exception as e:
        return JsonResponse({"history": [], "error": str(e)})
    

# ✅ Delete History from DB
def delete_history(request, id):
    if request.method == "DELETE":
        try:
            ChatHistory.objects.get(id=id).delete()
            return JsonResponse({"message": "Deleted ✅"})
        except:
            return JsonResponse({"message": "Not found ❌"})
    return JsonResponse({"message": "Invalid request"})


import mimetypes
import base64

def upload_pdf(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            doc = form.save()
            file_path = doc.file.path
            filename = doc.file.name.split('/')[-1].split('\\')[-1]
            mime_type, _ = mimetypes.guess_type(file_path)

            # ── IMAGE FILE ──────────────────────────────
            if mime_type and mime_type.startswith('image/'):
                try:
                    # Read and encode the actual image
                    with open(file_path, "rb") as img_file:
                        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

                    # Get user's question or use default
                    prompt = request.POST.get("question", "Describe this image in detail. If it contains an animal, identify the exact breed or species.")

                    # Call the correct function that sends the image
                    summary = get_answer_with_image(prompt, img_base64, mime_type)

                    ChatHistory.objects.create(
                        question=f"🖼️ {filename}",
                        answer=summary
                    )
                    return JsonResponse({"message": summary})

                except Exception as e:
                    return JsonResponse({"message": f"❌ Image processing failed: {str(e)}"})

            # ── PDF / TEXT FILE ─────────────────────────
            text = extract_text_from_pdf(file_path)

            if not text or text.strip() == "":
                return JsonResponse({"message": "❌ Could not extract text from PDF."})

            chunks = [chunk for chunk in text.split("\n") if chunk.strip()]

            if not chunks:
                return JsonResponse({"message": "❌ PDF has no readable text."})

            # Store embeddings
            embeddings = get_embeddings(chunks)
            if embeddings and len(embeddings) > 0:
                store_embeddings(embeddings, chunks)

            # Trim text to avoid token overflow
            trimmed_text = text[:6000]
            if len(text) > 6000:
                trimmed_text += "\n\n[Document trimmed due to length]"

            prompt = f"""The user uploaded a PDF document. Here is its content:

---
{trimmed_text}
---

Please do the following:
1. Give a brief overview of what this document is about
2. List the key topics or sections found
3. Highlight the most important points or findings
4. If it contains an animal — identify the exact breed/species
Format your response clearly using headings and bullet points."""

            try:
                summary = get_answer(prompt, [])

                ChatHistory.objects.create(
                    question=f"📄 {filename}",
                    answer=summary
                )

                return JsonResponse({"message": summary})
            except Exception as e:
                return JsonResponse({"message": f"❌ AI summary failed: {str(e)}"})

        return JsonResponse({"message": "❌ Invalid file."})

    return JsonResponse({"message": "Invalid request"})



# ✅ Summarization
def summarize_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            text = data.get("text")
            if not text:
                return JsonResponse({"summary": "No text provided."})
            summary = summarize_text(text)
            return JsonResponse({"summary": summary})
        except Exception as e:
            return JsonResponse({"summary": f"Error: {str(e)}"})
    return JsonResponse({"summary": "Invalid request"})


# ✅ Quiz
def quiz_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            text = data.get("text")
            if not text:
                return JsonResponse({"quiz": "No text provided."})
            quiz = generate_quiz(text)
            return JsonResponse({"quiz": quiz})
        except Exception as e:
            return JsonResponse({"quiz": f"Error: {str(e)}"})
    return JsonResponse({"quiz": "Invalid request"})


@csrf_exempt
def transcribe_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({'error': 'No audio file received'}, status=400)

    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
        for chunk in audio_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        result = whisper_model.transcribe(tmp_path, fp16=False)
        transcript = result['text'].strip()
        return JsonResponse({'transcript': transcript})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@csrf_exempt
def firebase_login(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "error": "Invalid request"
        })

    try:

        data = json.loads(request.body)

        id_token = data.get("id_token")

        if not id_token:

            return JsonResponse({
                "success": False,
                "error": "No token provided"
            })

        decoded_token = verify_firebase_token(id_token)

        if not decoded_token:

            return JsonResponse({
                "success": False,
                "error": "Invalid Firebase token"
            })

        email = decoded_token.get("email")

        name = decoded_token.get("name", "")

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                "email": email,
                "first_name": name
            }
        )

        login(request, user)

        return JsonResponse({
            "success": True,
            "email": email,
            "name": name
        })

    except Exception as e:

        print("Firebase Login Error:", e)

        return JsonResponse({
            "success": False,
            "error": str(e)
        })

# ─── FLASHCARDS ──────────────────────────────────────────

@require_POST
def generate_flashcards(request):
    try:
        data = json.loads(request.body)
        text = data.get("text", "")
        topic = data.get("topic", "General")

        if not text:
            return JsonResponse({"success": False, "error": "No text provided"}, status=400)

        cards = generate_flashcards_from_text(text, topic)
        save_flashcards(None, cards, topic)  # None = no Django user (Firebase handles auth)

        return JsonResponse({"success": True, "flashcards": cards})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def my_flashcards(request):
    flashcards = Flashcard.objects.filter(user=None).order_by("-created_at")
    return render(request, "chatbot/flashcards.html", {"flashcards": flashcards})


@require_POST
def mark_flashcard(request, pk):
    try:
        data = json.loads(request.body)
        fc = Flashcard.objects.get(pk=pk)
        fc.is_mastered = data.get("mastered", False)
        fc.times_reviewed += 1
        fc.last_reviewed = timezone.now()
        fc.save()
        return JsonResponse({"success": True})
    except Flashcard.DoesNotExist:
        return JsonResponse({"success": False, "error": "Flashcard not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ─── ANALYTICS ───────────────────────────────────────────

def analytics_dashboard(request):
    try:
        data = get_analytics_data(None)  # No Django user
        return render(request, "chatbot/analytics.html", {"analytics": data})
    except Exception as e:
        return render(request, "chatbot/analytics.html", {"analytics": {}})


def analytics_api(request):
    try:
        data = get_analytics_data(None)  # No Django user
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)