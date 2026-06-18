def generate_quiz(text):
    sentences = text.split('.')
    questions = []

    for i, sentence in enumerate(sentences[:5]):
        questions.append(f"Q{i+1}: What is meant by: {sentence.strip()}?")

    return questions