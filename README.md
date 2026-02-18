Brazilian Jiu-Jitsu Knowledge Assistant (v1.0.0)

A full-stack AI app that answers Brazilian Jiu-Jitsu questions using a strict RAG (Retrieval-Augmented Generation) pipeline.

The assistant only responds using a small curated knowledge base.
If the answer isn’t in the documents, it says: “I don’t know.”

Live Demo: 

Tech Stack
Frontend: React, External CSS styling, Smooth container-level scrolling, Loading state and error handling
Backend: FastAPI, OpenAI Embeddings API, Cosine similarity retrieval, SlowAPI rate limiting

What This Project Shows
React frontend
FastAPI backend
OpenAI embeddings
Manual cosine similarity search
Top-k retrieval
Prompt augmentation
Rate limiting + cost safeguards

How It Works
Documents are split into chunks.
Each chunk is converted into an embedding.
User questions are embedded.
The most similar chunks are retrieved.
Those chunks are injected into the prompt.
The model answers using only that context.
No context → no answer. 