from transformers import pipeline

summarizer = pipeline(
    "text-generation",
    model="gpt2"
)

def summarize_text(text):
    result = summarizer(
        "Summarize this: " + text,
        max_length=100,
        do_sample=False
    )
    return result[0]['generated_text']