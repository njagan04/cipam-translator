from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from gradio_client import Client, handle_file
import os
import uuid
from pydantic import BaseModel
import rag_service

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Gradio Client ----------------
client = Client("Sudhan26/Text-Translation")

# ---------------- Allowed Languages ----------------
ALLOWED_LANGS = [
    "Tamil","Hindi","Telugu","Malayalam","Kannada",
    "Marathi","Bengali","Gujarati","Punjabi","Urdu"
]

# ---------------- TEXT TRANSLATION ----------------
@app.post("/translate-text")
async def translate_text(
    text: str = Form(...),
    lang: str = Form(...)
):
    # ✅ Validate language
    if lang not in ALLOWED_LANGS:
        raise HTTPException(status_code=400, detail="Invalid language selected")

    # ✅ Validate text
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        result = client.predict(
            text=text,
            lang=lang,
            api_name="/translate_text"
        )

        return {
            "success": True,
            "translated_text": result[0],
            "stats": result[1]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


# ---------------- FILE TRANSLATION ----------------
@app.post("/translate-file")
async def translate_file(
    file: UploadFile = File(...),
    lang: str = Form(...)
):
    # ✅ Validate language
    if lang not in ALLOWED_LANGS:
        raise HTTPException(status_code=400, detail="Invalid language selected")

    # ✅ Validate file type
    if not (file.filename.endswith(".txt") or file.filename.endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Only TXT and PDF files are allowed")

    # ✅ Unique temp file (prevents overwrite issues)
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = temp_filename

    try:
        # Save file temporarily
        with open(file_path, "wb") as f:
            f.write(await file.read())

        result = client.predict(
            file=handle_file(file_path),
            lang=lang,
            api_name="/translate_file"
        )

        return {
            "success": True,
            "translated_content": result[0],
            "download_file": result[1]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File translation failed: {str(e)}")

    finally:
        # ✅ Always clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)


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
        
    # We will pass the requested language from the frontend to ensure output matches the selected translation language
    answer = rag_service.chat_with_document(req.query, req.lang)
    return {"success": True, "answer": answer}