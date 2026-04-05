from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import fitz  # PyMuPDF
from sarvamai import SarvamAI
from dotenv import load_dotenv
import os
import time
import rag_service
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Sarvam Client Setup ----------------
def get_sarvam_client():
    # Support both SARVAM_API_KEY and KEY depending on user .env
    key = os.getenv("SARVAM_API_KEY", os.getenv("KEY"))
    if not key:
        raise HTTPException(status_code=500, detail="Sarvam API Key is missing. Please set SARVAM_API_KEY or KEY in backend/.env")
    return SarvamAI(api_subscription_key=key)

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
    client = get_sarvam_client()
    
    # Intelligently split text by paragraphs/sentences (no word breaks)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=450, chunk_overlap=0)
    chunks = text_splitter.split_text(text)
    
    lang_code = SARVAM_LANG_MAP.get(target_lang, "hi-IN")
    source_lang_code = SARVAM_LANG_MAP.get(source_lang, "en-IN") if source_lang != "English" else "en-IN"
    
    translated_pieces = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        try:
            # Native Sarvam AI rapid translation
            response = client.text.translate(
                input=chunk,
                source_language_code=source_lang_code,
                target_language_code=lang_code,
                model="mayura:v1"
            )
            translated_pieces.append(response.translated_text)
            time.sleep(0.3)  # Small delay to prevent API rate-limit drops
        except Exception as e:
            raise Exception(f"Sarvam translation failed on chunk. Details: {str(e)}")
            
    return "\n\n".join(translated_pieces)

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
        translated = translate_long_text(text, lang, source_lang)
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
            pdf = fitz.open(stream=file_bytes, filetype="pdf")
            for page in pdf:
                content += page.get_text() + "\n"

        if not content.strip():
            raise HTTPException(status_code=400, detail="File is completely empty or cannot be read")

        translated_content = translate_long_text(content, lang)

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
    
    success = rag_service.index_document(req.text)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to index document. Check server logs.")
    
    return {"success": True, "message": "Document indexed for RAG"}

@app.post("/chat-document")
async def chat_document_api(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    answer = rag_service.chat_with_document(req.query, req.lang)
    return {"success": True, "answer": answer}