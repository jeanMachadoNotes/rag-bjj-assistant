# Brazilian Jiu-Jitsu Knowledge Assistant

An agent-orchestrated Retrieval-Augmented Generation (RAG) system built with React, FastAPI, LangChain, ChromaDB, and OpenAI embeddings.

This project demonstrates the architectural evolution of a production-style RAG application:
Manual Retrieval → Persistent Embeddings → Vector Database → Agentic Tool-Calling RAG



**Live Demo:** 


## Overview

This application answers questions about Brazilian Jiu-Jitsu using a strictly grounded RAG pipeline.

In v1.3.0, the system was upgraded to a LangChain tool-calling agent. The agent dynamically decides when to query a Chroma vector database and is required to retrieve context before making factual claims about the knowledge base.

The system enforces strict grounding:
- All factual answers must originate from retrieved chunks.
- If no relevant context is found, the assistant responds with "I don't know."
- Non-knowledge small talk is allowed without retrieval.

## Architecture

Frontend:
- React (Create React App)
- Mobile-optimized UI
- In-app versioning and changelog modal

Backend:
- FastAPI
- LangChain Agent (tool-calling)
- ChromaDB vector database
- OpenAI embeddings
- Strict retrieval enforcement
- Rate limiting (10 req/min/IP)

## Agent Flow:

User Message
    ↓
LangChain Agent
    ↓
If factual BJJ question → Call rag_search_tool
    ↓
ChromaDB vector query (top-3 cosine similarity)
    ↓
Context returned to agent
    ↓
Grounded response generation

## 🛡️ Security Testing

This project includes comprehensive security testing tools to assess prompt injection vulnerabilities:

### Quick Start
```bash
# Run automated security tests
cd backend
python security_test.py
```

### Testing Resources
- **SECURITY_TESTING_GUIDE.md** - Complete guide to running security tests
- **QUICK_MANUAL_TESTS.md** - 5-minute manual test checklist
- **SECURITY_TEST_REPORT.md** - Detailed vulnerability assessment with 23 test cases
- **backend/security_test.py** - Automated testing script
- **backend/security_improvements.py** - Enhanced security implementations

### What's Tested
- ✅ System prompt leaking attacks
- ✅ Role/instruction injection
- ✅ Unicode homograph bypasses
- ✅ Context boundary manipulation
- ✅ RAG-specific exploits
- ✅ Obfuscation techniques
- ✅ Multi-turn attacks

### Current Security Features
- Input pattern filtering
- Special character detection
- Rate limiting (10 req/min/IP)
- Chunk trust scoring
- Agent-based architecture with strict rules
- System prompt separation

For detailed security information, see [SECURITY_TESTING_GUIDE.md](SECURITY_TESTING_GUIDE.md).