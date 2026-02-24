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
import chromadb
from chromadb.config import Settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "embeddings.json")


# Load enviroment variables from .env
load_dotenv()

# Sets up FastAPI app, that will receive requests, hold your routes (like /chat), settings (like CORS).
app = FastAPI()
@app.on_event("startup")
def _startup() -> None:
    load_embeddings_into_chroma()

# Chroma Setup v1.2.0
CHROMA_DIR = "chroma_db" 

chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False),
)

collection = chroma_client.get_or_create_collection(
    name="rag_chunks_v1",
    metadata={"hnsw:space": "cosine"},
)

def load_embeddings_into_chroma() -> None:
    """
    Loads embeddings.json into Chroma once (if collection is empty).
    Expected embeddings.json format (based on v1.1.0)
    [
        {"id": "...", "text": "...", "embedding": [...]},
        ...
    ]
    """
    if not os.path.exists(EMBEDDINGS_PATH):
        print("embeddings.json not found; killing Chroma load.")
        return
    
    # If already loaded, do nothing
    try:
        existing = collection.count()
    except Exception as e:
        print("Chroma count() failed:", e)
        existing = 0

    if existing > 0:
        print(f"Chroma already has {existing} items; killing load.")
        return
    
    with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    ids: list[str] = []
    docs: list[str] = []
    embeds: list[list[float]] = []

    for i, item in enumerate(data):
        chunk_id = item.get("id") or f"chunk_{i}"
        text = item.get("text") or item.get("chunk") or ""
        embedding = item.get("embedding") or item.get("vector")

        if not text or not embedding:
            #Skip bad rows (keeps app running)
            continue

        ids.append(str(chunk_id))
        docs.append(text)
        embeds.append(embedding)

    if not ids:
        print("No valid chunks found in embeddings.json; nothing loaded.")
        return
    
    collection.add(ids=ids, documents=docs, embeddings=embeds)
    print(f"Loaded {len(ids)} chunks into Chroma.")
                                                    



# Settings #s
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

# Splits document into chunks
def chunk_text(text):
    sentences = text.replace("\n", " ").split(".")
    chunks = []

    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned:
            chunks.append(cleaned + ".")
    
    return chunks

# Embeds chunks using OpenAI model
def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# Manual similarity check replaced by Chromadb
# def cosine_similarity(vec1, vec2):
#     dot_product = sum(a * b for a, b in zip(vec1, vec2))
#     norm1 = math.sqrt(sum(a * a for a in vec1))
#     norm2 = math.sqrt(sum(b * b for b in vec2))
#     return dot_product / (norm1 * norm2)


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


        # --------------------------------

        # Manual similarity check, retrieval replaced by Chromadb
        # # Compute similarity scores
        # scored_chunks = []
        # for item in chunk_embeddings:
        #     chunk = item["chunk"]
        #     embedding = item["embedding"]
        #     score = cosine_similarity(question_embedding, embedding)
        #     scored_chunks.append((score, chunk))

        # # Sort by highest similarity (score)
        # scored_chunks.sort(reverse=True)

        # # Take the Top 3
        # top_chunks = scored_chunks[:3]

        # context = "\n".join([chunk for _, chunk in top_chunks])

        # -------------------------------

        # Retrieving Top 3 (high score) chunks from Chromadb
        # Ask Chroma for the top 3 most similar chunks
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=3,
            include=["documents", "distances", "data"],
        )

        # Chroma returns lists-of-lists (because it supports batch queries)
        retrieved_docs = results.get("documents", [[]])[0]
        retrieved_ids = results.get("ids", [[]])[0]
        retrieved_distances = results.get("distances", [[]])[0]

        # If retrieval fails, keep strict behavior
        if not retrieved_docs or all((d is None or d.strip() == "") for d in retrieved_docs):
            return {"response": "I dont know."}
        
        # Build context from retrieved documents
        context = "\n".join(retrieved_docs)
            
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