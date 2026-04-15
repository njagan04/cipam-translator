# CIPAM Multilingual Translator — Backend & RAG System Documentation

> **Purpose:** In-depth technical reference for project review. Covers architecture, technology choices, advantages, and design decisions.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Backend Architecture](#3-backend-architecture)
4. [Translation Pipeline — Sarvam AI](#4-translation-pipeline--sarvam-ai)
5. [RAG System — Document Chat](#5-rag-system--document-chat)
6. [API Endpoints Reference](#6-api-endpoints-reference)
7. [Deployment Setup](#7-deployment-setup)
8. [Design Decisions & Advantages](#8-design-decisions--advantages)
9. [Key Limitations & Trade-offs](#9-key-limitations--trade-offs)

---

## 1. Project Overview

The **CIPAM Multilingual Translator** is an AI-powered web application designed to:

- **Translate** text and documents (TXT, PDF) into 9 Indian regional languages using Sarvam AI.
- **Chat with documents** — users can ask questions about a translated/uploaded document in any target language, powered by Google Gemini and a custom RAG pipeline.

The system is targeted at CIPAM (Cell for IPR Promotion and Management) use cases — helping users understand intellectual property documents in their native Indian language.

---

## 2. Technology Stack

### Backend

| Component | Technology | Why Chosen |
|---|---|---|
| Web Framework | **FastAPI** | Async-first, high performance, auto-generates OpenAPI docs, ideal for ML/AI APIs |
| ASGI Server | **Uvicorn** | Production-grade async server for FastAPI, low latency |
| Translation API | **Sarvam AI (`sarvamai`)** | Purpose-built for Indian languages, high accuracy for Indic scripts |
| PDF Parsing | **PyMuPDF (`fitz`)** | Fastest Python PDF library, in-memory parsing with no temp files |
| LLM for Q&A | **Google Gemini 2.5 Flash** | Fast, cost-effective, multimodal, strong reasoning for document Q&A |
| LLM Framework | **LangChain** | Standardized chain/prompt interface for connecting LLM components |
| Environment Config | **python-dotenv** | Secure API key management via `.env` files |
| Multipart Forms | **python-multipart** | Required for FastAPI file upload handling |

### RAG-Specific

| Component | Technology | Why Chosen |
|---|---|---|
| LLM Interface | **langchain-google-genai** | Official LangChain adapter for Google Gemini models |
| Prompt Templates | **LangChain PromptTemplate** | Structured, reusable prompt composition |
| Retrieval | **Custom TF-based retriever** | Zero-dependency, ultra-fast, no GPU needed |
| Output Parsing | **LangChain StrOutputParser** | Clean string extraction from LLM responses |

---

## 3. Backend Architecture

### File Structure
```
backend/
├── main.py          # FastAPI app — all endpoints, Sarvam translation logic
├── rag_service.py   # RAG pipeline — indexing, retrieval, Gemini Q&A
├── requirements.txt # Python dependencies
└── .env             # Secret API keys (not committed to Git)
```

### How the Server Starts
```
uvicorn main:app --host 0.0.0.0 --port 8080
```

1. FastAPI app initializes
2. CORS middleware is configured (allows all origins for cross-domain frontend access)
3. `rag_service` module is **eagerly imported** at startup — this pre-loads LangChain so the first user request is not slow
4. Server listens on port 8080

### Request Flow (Translation)
```
User (Browser) → Frontend (React)
             → POST /translate-text or /translate-file
             → FastAPI (main.py)
             → get_sarvam_client() — reads SARVAM_API_KEY from env
             → translate_long_text() — chunks text, parallel translation
             → Sarvam AI Cloud API
             → Response assembled → returned to Frontend
```

### Request Flow (Document Chat)
```
User uploads file → Frontend
               → POST /index-document (with extracted text)
               → rag_service.index_document() — pure Python chunking
               → chunks stored in memory (chunks_global)

User asks question → Frontend
               → POST /chat-document (query + language)
               → rag_service.chat_with_document()
               → retrieve_top_k() — TF matching → best chunks
               → Gemini 2.5 Flash → answer in selected language
               → returned to Frontend
```

---

## 4. Translation Pipeline — Sarvam AI

### What is Sarvam AI?
Sarvam AI is an Indian AI company that specializes in **large language models and APIs for Indian languages**. Their translation model (`mayura:v1`) is specifically trained on Indic language pairs, making it far more accurate for languages like Tamil, Telugu, Kannada, etc., compared to general-purpose translators.

### Language Support
```python
SARVAM_LANG_MAP = {
    "Hindi":     "hi-IN",
    "Tamil":     "ta-IN",
    "Telugu":    "te-IN",
    "Kannada":   "kn-IN",
    "Malayalam": "ml-IN",
    "Marathi":   "mr-IN",
    "Gujarati":  "gu-IN",
    "Punjabi":   "pa-IN",
    "Bengali":   "bn-IN",
    "Urdu":      "hi-IN"  # Fallback — Sarvam does not officially support ur-IN
}
```

### Chunking Strategy
Sarvam AI has a **character limit per API request**. Large documents must be split into chunks and translated separately.

```python
limit = 850  # characters per chunk
```

**Why 850?**
- Fits comfortably under Sarvam's network/API limits
- Reduces total number of API requests while staying within bounds
- Balances latency vs. cost

**Chunking Algorithm:**
- Text is split word-by-word (not character-by-character) to avoid cutting words mid-way
- Each chunk accumulates words until the 850-char threshold is reached
- When the threshold is hit, the chunk is saved and a new one starts

### Parallel Translation
```python
with ThreadPoolExecutor(max_workers=7) as executor:
    futures = [executor.submit(translate_single_chunk, i, chunk) for i, chunk in enumerate(valid_chunks)]
```

**Why parallel?**
- A large document may produce 20–50 chunks
- Sequential translation would take 20–50x longer
- `ThreadPoolExecutor` with **7 workers** was chosen as the sweet spot:
  - Respects Sarvam's rate limits (too many concurrent = 429 errors)
  - Fits within standard 60-second cloud server timeouts (e.g., Vercel, Leapcell)
  - `time.sleep(0.01)` adds a tiny stagger to prevent simultaneous bursts

**Result reassembly:**
- Each chunk is tagged with its original index `(idx, translated_text)`
- Chunks are reassembled in order regardless of which thread finished first
- Final output is joined with `\n\n` to preserve paragraph separation

### Error Handling in Translation
```python
except Exception as e:
    return (idx, f"[Error predicting text logic: {str(e)}]")
```

- If a single chunk fails (e.g., API rate limit), that chunk returns a visible error message
- The rest of the document still translates successfully — **graceful degradation**
- The server returns `200 OK` even if some chunks have errors (since partial translation is better than total failure)

---

## 5. RAG System — Document Chat

### What is RAG?
**Retrieval-Augmented Generation (RAG)** is an AI technique that combines:
1. **Retrieval** — Find the most relevant parts of a document for a given question
2. **Generation** — Feed those parts to an LLM (Gemini) to produce a grounded, accurate answer

This prevents the LLM from "hallucinating" answers that are not in the document, since it only sees the document's actual content.

### Why RAG instead of sending the full document to Gemini?
| Approach | Problem |
|---|---|
| Send full document to Gemini | Cost scales with document size, context window limits, slow |
| RAG — send only relevant chunks | Cheap, fast, accurate, no context limit issues |

---

### Step 1: Indexing (`index_document`)

When a user uploads and translates a document, the text is sent to `/index-document`.

```python
chunks_global = []  # In-memory store

def index_document(text: str) -> bool:
    words = text.split(" ")
    # Word-by-word chunking with 1000-char limit
    limit = 1000
    ...
    chunks_global.append(" ".join(current))
```

**What happens:**
- The full document text is split into ~1000-character chunks
- Chunks are stored in a **Python list in server memory** (`chunks_global`)
- No database, no disk writes, no ML models used — **pure Python**

**Why not FAISS/vector embeddings?**
- FAISS requires loading heavy ML embedding models (hundreds of MB)
- For document sizes in this use case, TF matching is fast enough
- Eliminates GPU dependency and massive cold-start times
- Deliberately avoids heavy dependencies for speed and cost

---

### Step 2: Retrieval (`retrieve_top_k`)

```python
def retrieve_top_k(query: str, k: int = 4) -> str:
    query_words = set([w.strip().lower() for w in query.split()])
    scores = []
    for chunk in chunks_global:
        chunk_words = chunk.lower().split()
        score = sum(chunk_words.count(qw) for qw in query_words)
        scores.append((score, chunk))
    scores.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join([c for s, c in scores[:min(k, len(scores))]])
```

**Algorithm: Term Frequency (TF) Matching**
- Each query word is counted in every chunk
- Chunks with the highest total keyword count are ranked highest
- Top `k=4` chunks are selected and returned as context

**Why TF matching?**
- Zero external dependencies
- Runs in milliseconds even for large documents
- No GPU, no model loading, no network calls
- Sufficient for keyword-heavy legal/IP documents like CIPAM materials

---

### Step 3: Generation (`chat_with_document`)

```python
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

context = retrieve_top_k(query, k=4)

template = f"""You are an expert AI assistant specializing in answering questions 
based on the provided CIPAM Intellectual Property document.
Use the following pieces of retrieved context to answer the question at the end.
...
CRITICAL INSTRUCTION: You MUST provide your final answer entirely in: {lang}.

Context:
{context}

Question: {query}
Answer in {lang}:"""

rag_chain = prompt | llm | StrOutputParser()
response = rag_chain.invoke({})
```

**What happens:**
1. Top 4 relevant chunks are retrieved by TF matching
2. A structured prompt is built with the context + user's question
3. Gemini 2.5 Flash generates the answer **strictly based on the provided context**
4. `StrOutputParser` extracts clean string output from the LLM response
5. The answer is returned in the user's selected language (enforced by the prompt)

**Why Gemini 2.5 Flash?**
| Reason | Detail |
|---|---|
| Speed | "Flash" models are optimized for low latency |
| Cost | Much cheaper than Gemini Pro/Ultra for high-volume Q&A |
| Multilingual | Excellent support for Indian language output |
| Accuracy | Strong reasoning for document-grounded Q&A |

**Why `temperature=0.3`?**
- Lower temperature = more deterministic, factual answers
- Prevents the model from "getting creative" with legal/IP content
- Balance between strict factuality (0.0) and natural language quality (1.0)

---

### LangChain Pipeline: `prompt | llm | StrOutputParser()`

This is a **LangChain Expression Language (LCEL)** chain — a modern, composable way to build LLM pipelines.

```
PromptTemplate  →  ChatGoogleGenerativeAI  →  StrOutputParser
(formats prompt)    (calls Gemini API)        (extracts string)
```

**Advantages of LCEL:**
- Clean, readable pipeline definition
- Easy to swap components (e.g., replace Gemini with another LLM)
- Built-in streaming support (can be enabled later)
- Standardized interface across all LangChain components

---

## 6. API Endpoints Reference

| Method | Endpoint | Purpose | Input | Output |
|---|---|---|---|---|
| `GET` | `/` | Health check | — | `{"message": "Translation API is running"}` |
| `POST` | `/translate-text` | Translate raw text | `text`, `lang`, `source_lang` (form) | `{"success": true, "translated_text": "..."}` |
| `POST` | `/translate-file` | Translate TXT/PDF file | `file` (upload), `lang` (form) | `{"success": true, "translated_content": "..."}` |
| `POST` | `/index-document` | Index document for RAG | `{"text": "..."}` (JSON) | `{"success": true, "message": "..."}` |
| `POST` | `/chat-document` | Ask question about indexed doc | `{"query": "...", "lang": "..."}` (JSON) | `{"success": true, "answer": "..."}` |

---

## 7. Deployment Setup

### Platform: Leapcell (Backend)

- Leapcell is a cloud hosting platform for Python backends
- Deployed as a **persistent service** (not serverless lambda) — keeps `chunks_global` state in memory between requests
- **Auto-deploys** when changes are pushed to the connected GitHub branch

### Environment Variables (set in Leapcell dashboard)

| Variable | Purpose |
|---|---|
| `SARVAM_API_KEY` | Authenticates requests to Sarvam AI translation API |
| `GOOGLE_API_KEY` | Authenticates requests to Google Gemini API for document Q&A |

> These are never committed to Git. The `.env` file is listed in `.gitignore`.

### Start Command
```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port 8080
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows frontend on any domain to call the API
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 8. Design Decisions & Advantages

### No Database Required
- Document chunks are stored **in-memory** (`chunks_global` list)
- Eliminates the need for PostgreSQL, Redis, or any external database
- Reduces infrastructure complexity and cost significantly
- Trade-off: chunks reset on server restart (acceptable for session-based use)

### No GPU / No Heavy ML Models for Retrieval
- Standard RAG systems use FAISS + sentence-transformers (requires 500MB+ model downloads)
- This system uses pure Python TF matching — works on any CPU-only server
- Dramatically reduces cold-start time and hosting cost

### Parallel Translation with ThreadPoolExecutor
- Documents are translated in parallel using 7 concurrent workers
- Large documents translate in seconds instead of minutes
- Tiny `time.sleep(0.01)` stagger prevents rate-limit spikes

### Lazy PDF Parsing
```python
import fitz  # Only imported when a PDF is actually uploaded
```
- PyMuPDF is only imported when a PDF file is actually uploaded
- Reduces initial server startup time

### Eager RAG Service Loading
```python
import rag_service  # Pre-loaded at startup
```
- LangChain is imported at boot time so the first user request is not slow
- Removes user-perceived latency on the first document indexing

### Graceful Translation Error Handling
- If one chunk fails during translation, the error is embedded in that chunk only
- The rest of the document still translates successfully
- User sees mostly correct output rather than a total failure

---

## 9. Key Limitations & Trade-offs

| Limitation | Impact | Possible Future Fix |
|---|---|---|
| In-memory chunk storage | Lost on server restart; shared global state across users | Use Redis or per-session storage |
| TF retrieval (no semantic search) | May miss relevant chunks if synonyms or paraphrasing are used | Add FAISS + sentence-transformers for vector search |
| No streaming for chat answers | User waits for full Gemini response before seeing anything | Enable LangChain streaming with Server-Sent Events |
| CORS `allow_origins=["*"]` | Anyone can call the API; security risk | Restrict to specific frontend domain in production |
| Urdu maps to Hindi (`hi-IN`) | Urdu output rendered in Hindi script | Await official Sarvam support for `ur-IN` |
| `chunks_global` is a module-level global | Not thread-safe for simultaneous multi-user indexing | Add locking or session-based chunk storage |

---

*Documentation prepared for CIPAM Translator — Backend v1.0*  
*Stack: FastAPI · Uvicorn · Sarvam AI (mayura:v1) · Google Gemini 2.5 Flash · LangChain LCEL · PyMuPDF · Leapcell*
