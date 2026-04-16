from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time

from dotenv import load_dotenv
load_dotenv()

try:
    import rag_service  # Pre-load at startup to avoid cold import delay on first request
    print("rag_service loaded successfully at startup.")
except Exception as e:
    print(f"WARNING: rag_service failed to load at startup: {e}. Document chat will be unavailable.")
    rag_service = None

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Sarvam Client Setup ----------------
def get_sarvam_client():
    from sarvamai import SarvamAI
    # Support both SARVAM_API_KEY and KEY depending on user .env
    key = os.getenv("SARVAM_API_KEY", os.getenv("KEY"))
    if not key:
        raise HTTPException(status_code=500, detail="Sarvam API Key is missing. Please set SARVAM_API_KEY or KEY in backend/.env")
    return SarvamAI(api_subscription_key=key.strip())

SARVAM_LANG_MAP = {
    "Hindi": "hi-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Kannada": "kn-IN",
    "Malayalam": "ml-IN",
    "Marathi": "mr-IN",
    "Gujarati": "gu-IN",
    "Punjabi": "pa-IN",
    "Bengali": "bn-IN",
    "Urdu": "hi-IN" # Fallback to Hindi if requested since Sarvam doesn't officially map ur-IN in this wrapper
}

def translate_long_text(text: str, target_lang: str, source_lang: str = "English") -> str:
    """Chunks text seamlessly to fit within Sarvam AI translation limits."""
    from concurrent.futures import ThreadPoolExecutor
    
    client = get_sarvam_client()
    
    # Cloud Threshold Optimization: 1000 natively fits under Sarvam network limits while dramatically reducing total requests
    limit = 1000
    words = text.split(' ')
    valid_chunks = []
    current_chunk = []
    current_length = 0
    for word in words:
        if current_length + len(word) + 1 > limit and current_chunk:
            valid_chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    if current_chunk:
        valid_chunks.append(' '.join(current_chunk))
        
    lang_code = SARVAM_LANG_MAP.get(target_lang, "hi-IN")
    source_lang_code = SARVAM_LANG_MAP.get(source_lang, "en-IN") if source_lang != "English" else "en-IN"
        
    valid_chunks = [c for c in valid_chunks if c.strip()]
    if not valid_chunks:
        return ""

    def translate_single_chunk(idx, text_chunk):
        try:
            # Native Sarvam AI rapid translation
            response = client.text.translate(
                input=text_chunk,
                source_language_code=source_lang_code,
                target_language_code=lang_code,
                model="mayura:v1"
            )
            return (idx, response.translated_text)
        except Exception as e:
            # If a strict failure happens, gracefully let the document pass with a warning, or raise
            return (idx, f"[Error predicting text logic: {str(e)}]")

    translated_pieces = [""] * len(valid_chunks)
    
    # 7 worker threads mathematically balances Sarvam rate limits against standard Cloud Vercel 60s Timeouts for massive files
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = []
        for i, chunk in enumerate(valid_chunks):
            futures.append(executor.submit(translate_single_chunk, i, chunk))
            time.sleep(0.01) # Tiny buffer to prevent instantly slamming server with 15 simultaneous spikes
            
        for future in futures:
            idx, result_text = future.result()
            translated_pieces[idx] = result_text

    return "\n\n".join(translated_pieces)

def translate_with_gemini(text: str, target_lang: str, source_lang: str = "English") -> str:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    
    # 2.5 flash is extremely fast, cheap, and has a massive context window natively built for huge text
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
    template = """You are a highly accurate professional language translator.
You must translate the completely provided text from {source_lang} to {target_lang}.
Provide ONLY the translated text without any conversational filler, explanations, or extra markdown wrapping if not present in the source.

Original Text:
{text}
"""
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": text, "source_lang": source_lang, "target_lang": target_lang})

def smart_translate(text: str, target_lang: str, source_lang: str = "English") -> str:
    # Approx 30,000 characters represents ~10 pages of typical PDF content
    limit_chars = 30000 
    
    if len(text) > limit_chars:
        print(f"Text too large ({len(text)} chars, > 10 pages). Falling back natively to Gemini Flash...")
        try:
            return translate_with_gemini(text, target_lang, source_lang)
        except Exception as e:
            print(f"Gemini fallback failed: {e}. Trying Sarvam array chunking as absolute last resort...")
            return translate_long_text(text, target_lang, source_lang)
    else:
        # Under 10 pages, continue using optimal Sarvam sequence
        return translate_long_text(text, target_lang, source_lang)

# ---------------- PROMPT ENGINEERING GATES ----------------
def precheck_text(text: str) -> bool:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
    template = """[Role]: You are an enterprise compliance validator and language detection engine.
[Task]: Evaluate the source text. Identify if the source language is strictly English. If it is English, output VALID. If it contains non-English source text, output INVALID.
[Format]: Output ONLY the word VALID or INVALID.

Text to evaluate:
{text}
"""
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    try:
        result = chain.invoke({"text": text[:2000]}).strip().upper()
        # Ensure exact match because the word 'VALID' is technically inside the word 'INVALID'!
        return result == "VALID"
    except Exception as e:
        print(f"Text precheck failed: {e}")
        return True # Failsafe open

def precheck_file(text: str) -> bool:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
    template = """[Context]: You are evaluating a document for the Cell for IPR Promotion and Management (CIPAM) or Intellectual Property Rights (IRM) backend system.
[Action]: Analyze the core subject matter of the provided document text. Check if the document discusses CIPAM, intellectual property, trademarks, IRM, or related compliance.
[Result]: If the context is valid and related, output VALID. If it is completely unrelated to CIPAM or IRM, output INVALID.

Document to evaluate:
{text}
"""
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    try:
        result = chain.invoke({"text": text[:5000]}).strip().upper()
        return result == "VALID"
    except Exception as e:
        print(f"File precheck failed: {e}")
        return True # Failsafe open

# ---------------- TEXT TRANSLATION ----------------
@app.post("/translate-text")
async def translate_text(
    text: str = Form(...),
    lang: str = Form(...),
    source_lang: str = Form("English")
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        # ---- RTF GATE ----
        if not precheck_text(text):
            return {
                "success": True,
                "translated_text": "crm info are in english only, so english translation only allowed",
                "stats": {"time": 0, "chars": len(text)}
            }

        translated = smart_translate(text, lang, source_lang)
        return {
            "success": True,
            "translated_text": translated,
            "stats": {"time": 0, "chars": len(text)} # Dummy stats to satisfy frontend
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- FILE TRANSLATION ----------------
@app.post("/translate-file")
async def translate_file(
    file: UploadFile = File(...),
    lang: str = Form(...)
):
    if not (file.filename.endswith(".txt") or file.filename.endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Only TXT and PDF files are allowed")

    try:
        content = ""
        # Parse natively in-memory (No messy temp file saving!)
        file_bytes = await file.read()
        
        if file.filename.endswith(".txt"):
            content = file_bytes.decode("utf-8")
        elif file.filename.endswith(".pdf"):
            import fitz # Lazy load PyMuPDF dynamically upon first PDF upload to save massive boot time
            pdf = fitz.open(stream=file_bytes, filetype="pdf")
            for page in pdf:
                content += page.get_text() + "\n"

        if not content.strip():
            raise HTTPException(status_code=400, detail="File is completely empty or cannot be read")

        # ---- CARE GATE ----
        if not precheck_file(content):
            return {
                "success": True,
                "aborted": True,
                "translated_content": "### 🛑 Security Gate Abort\nError: The uploaded file context is not based on CIPAM or IRM. Translation and Document Indexing aborted.",
                "download_file": None
            }

        translated_content = smart_translate(content, lang)

        return {
            "success": True,
            "translated_content": translated_content,
            "download_file": None  # Frontend handles local blob download logic
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File translation failed: {str(e)}")

# ---------------- HEALTH CHECK ----------------
@app.get("/")
def home():
    return {"message": "Translation API is running"}


# ---------------- RAG ENDPOINTS ----------------
class IndexRequest(BaseModel):
    text: str

class ChatRequest(BaseModel):
    query: str
    lang: str

@app.post("/index-document")
async def index_document_api(req: IndexRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # rag_service already loaded at startup
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service unavailable. Check server logs for import errors.")
    
    success = rag_service.index_document(req.text)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to index document. Check server logs.")
    
    return {"success": True, "message": "Document indexed for RAG"}

@app.post("/chat-document")
async def chat_document_api(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    # rag_service already loaded at startup
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service unavailable. Check server logs for import errors.")
    answer = rag_service.chat_with_document(req.query, req.lang)
    return {"success": True, "answer": answer}