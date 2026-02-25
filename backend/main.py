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
from pprint import pprint
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "embeddings.json")
APP_VERSION = "v1.3.0"

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

## Agent Tools
@tool
def rag_search(query: str, k: int = 3) -> dict:
    """
    Tool: search the knowledge base and return the top chunks.
    Returns: {"chunks": [{"id": str, "text": str, "distance": float[None], ...}]}
    """
    query = (query or "").strip()
    if not query:
        return {"chunks": []}
    
    # Debug Line
    print("TOOL CALLED rag_search_tool with query =", repr(query)) 

    # User query
    query_embedding = get_embedding(query)

    # Chromadb Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "distances"],
    )

    docs = (results.get("documents") or [[]])[0] or []
    ids = (results.get("ids")) or [[]][0] or []
    dists = (results.get("distances") or [[]])[0] or [] 

    chunks = []
    for i, doc in enumerate(docs):
        if not doc or not doc.strip():
            continue
        chunks.append({
            "id": str(ids[i]) if i < len(ids) else str(i),
            "text": doc,
            "distance": dists[i] if i < len(dists) else None,
        })
    return {"chunks": chunks}

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



# END POINTS

# Server health endpoint
@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION}
    


# Chat endpoint route (URL + Method)
@app.post("/chat")
@limiter.limit("10/minute")
def chat(request: Request, message: Message):
    # Input validation
    if len(message.text) > 500:
        return {"response": "Message too long. Please limit your question."}
    try:
        # Debug Line
        # print("INCOMING message.text=", repr(message.text))

        sys_prompt = """
        You are a friendly BJJ tutor.

        Rules:
        - If the user asks any BJJ / jiujitsu / ju jitsu or similar questions about technique/rules/training, you MUST call rag_search_tool before answering.
        - Use ONLY tool chunks for BJJ factual answers.
        - If the tool returns no chunks, say "I don't know." and ask one short follow-up question.
        - For greetings/small talk, you may respond without calling tools.
        - Seek to guide back the conversation to BJJ when asked a question that isn't relevant. You can be blunt about it.
        """
        
        # LangChain chat model (tool calling)
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )

        # Create Agent
        bjj_agent = create_agent(
            model=llm,
            tools=[rag_search],
            system_prompt=sys_prompt
        )
        
        # Debug Line
        # print("SENDING TO AGENT =", repr(message.text))

        # Invoke the agent with the user's real input
        response = bjj_agent.invoke({
            "messages": [{
                "role": "user", 
                "content": message.text
                }]
        })

        #Debug Line
        # pprint(response['messages'][-1].content)

        return {"response": response['messages'][-1].content}

    except Exception as e:
        return {"response": "Something went wrong. Please try again."}