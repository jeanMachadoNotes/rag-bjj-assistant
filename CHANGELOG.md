# Changelog

All notable changes to this project will be documented here.

---
# v.1.3.0 - Agentic RAG Integration

- Replaced direct LLM calls with a LangChain tool-calling agent
- Encapsulated vector retrieval as a structured RAG tool
- Maintained strict grounding: factual claims require retrieved context
- Improved conversational handling for non-knowledge queries
- UI/UX Improvements (icon button, mobile fixes, scroll modal)

# v1.2.0 - Vector Database Integration

- Replaced manual cosine retrieval with ChromaDB query
- Added Chroma persistent client + collection (local persistence; Render resets on restart)

## v1.1.0 – Persistent Embeddings

- Added file-based embedding persistence, Embeddings persist during runtime; persistent storage requires attached disk.
- Prevents regeneration on server restart
- Reduces startup time and OpenAI usage
- Introduced conditional embedding loading logic

## v1.0.1 – UI Improvements

- Added in-app changelog modal
- Added CHANGELOG.md to repository
- Minor UI refinements

## v1.0.0 – Initial Public Release

- Strict Retrieval-Augmented Generation (RAG) pipeline
- Curated Brazilian Jiu-Jitsu knowledge base ingestion
- Semantic chunking of source document
- Manual top-3 cosine similarity retrieval
- Strict context-only prompt enforcement
- Rate limiting and input validation
- Production deployment (Render + Vercel)

