from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "embeddings.json")

print("Embeddings path:", EMBEDDINGS_PATH)


# Load enviroment variables from .env
load_dotenv()

# Sets up FastAPI app, that will receive requests, hold your routes (like /chat), settings (like CORS).
app = FastAPI()

# Settings #
# Allows frontend (React) to talk to backend (Python)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://rag-bjj-assistant.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Rate Limiter settings
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"response": "Too many requests. Please wait a minute and try again."}
    )


# Create OpenAI client using API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Defines shape of data to be received
class Message(BaseModel):
    text: str




# Helper functions
def chunk_text(text):
    sentences = text.replace("\n", " ").split(".")
    chunks = []

    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned:
            chunks.append(cleaned + ".")
    
    return chunks

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


# Create Chunks
with open("documents/knowledge.txt", "r") as f:
        content = f.read()
        chunks = chunk_text(content)


# Load and Embed Documents
if os.path.exists(EMBEDDINGS_PATH):
    print("Loading precomputed embeddings...")
    with open(EMBEDDINGS_PATH, "r") as f:
        chunk_embeddings = json.load(f)
else:
    print("Generating embeddings for first time...")
    chunk_embeddings = []

    for chunk in chunks:
        embedding = get_embedding(chunk)
        chunk_embeddings.append({
            "chunk": chunk,
            "embedding": embedding
        })
    
    with open(EMBEDDINGS_PATH, "w") as f:
        json.dump(chunk_embeddings, f)



# Chat endpoint route (URL + Method)
@app.post("/chat")
@limiter.limit("10/minute")
def chat(request: Request, message: Message):
    # Input validation
    if len(message.text) > 500:
        return {"response": "Message too long. Please limit your question."}
    try:
        question_embedding = get_embedding(message.text)

        # Compute similarity scores
        scored_chunks = []
        for item in chunk_embeddings:
            chunk = item["chunk"]
            embedding = item["embedding"]
            score = cosine_similarity(question_embedding, embedding)
            scored_chunks.append((score, chunk))

        # Sort by highest similarity (score)
        scored_chunks.sort(reverse=True)

        # Take the Top 3
        top_chunks = scored_chunks[:3]

        context = "\n".join([chunk for _, chunk in top_chunks])

        # Open RAG design (flexible)
        #     prompt = f"""
        # Use the context below to answer the question.

        # Context:
        # {context}

        # Question:
        # {message.text}
        # """
            
        # Strict RAG (Document Only)
        prompt = f"""
You are a helpful assistant.
Answer the question using ONLY the context below.
If the anser is not containe din the context, say "I don't know."

Context:
{context}

Question:
{message.text}

"""

    
        # Send Users message to AI and store response
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
            
        )
        
        # Return AIs response
        return {"response": response.choices[0].message.content}

    except Exception as e:
        return {"response": "Something went wrong. Please try again."}