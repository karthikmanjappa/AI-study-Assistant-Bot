from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embeddings(text_chunks):
    # ✅ Convert to list so it works with FAISS
    return model.encode(text_chunks).tolist()