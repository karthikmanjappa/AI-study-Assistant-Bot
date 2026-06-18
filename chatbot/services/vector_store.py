import faiss
import numpy as np

index = None
stored_texts = []

def store_embeddings(embeddings, texts):
    global index, stored_texts

    # ✅ Convert to numpy array properly
    embeddings_array = np.array(embeddings).astype('float32')

    if embeddings_array.shape[0] == 0:
        return

    dim = embeddings_array.shape[1]  # ✅ use .shape not len()
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings_array)
    stored_texts = texts

def search(query_embedding, k=3):
    global index, stored_texts

    if index is None or len(stored_texts) == 0:
        return []

    query_array = np.array([query_embedding]).astype('float32')
    distances, indices = index.search(query_array, k)
    return [stored_texts[i] for i in indices[0] if i < len(stored_texts)]