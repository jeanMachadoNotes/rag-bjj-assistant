from openai import OpenAI
from dotenv import load_dotenv
import os
import math

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create chunks
def chunk_text(text):
    sentences = text.replace("\n", " ").split(". ")
    chunks = []

    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned:
            chunks.append(cleaned + ".")
    return chunks

# Creates embeddings
def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (norm1 * norm2)

if __name__ == "__main__":
    with open("documents/knowledge.txt", "r") as f:
        content = f.read()
    
    chunks = chunk_text(content)

    # Generate chunk embeddings
    chunk_embeddings = []
    for chunk in chunks:
        embedding = get_embedding(chunk)
        chunk_embeddings.append((chunk, embedding))

    # User question
    question = "What does RAG stand for?"
    question_embedding = get_embedding(question)

    print("\nSimilarity scores:\n")

    for chunk, embedding in chunk_embeddings:
        score = cosine_similarity(question_embedding, embedding)
        print(f"Score: {score:.4f} | Chunk: {chunk}")