# ==========================================================
# AI MULTILINGUAL TRANSLATION SYSTEM - FINAL VERSION
# ==========================================================

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from deep_translator import GoogleTranslator
import fitz
import io

app = FastAPI(title="AI Multilingual Translation System")

# ------------------ REQUEST MODEL ------------------

class TextData(BaseModel):
    text: str
    target_lang: str


# ------------------ HOME ------------------

@app.get("/")
def home():
    return {"message": "AI Translator API running successfully 🚀"}


# ------------------ LANGUAGES ------------------

@app.get("/languages")
def get_languages():
    return {
        "ta": "Tamil",
        "hi": "Hindi",
        "te": "Telugu",
        "ml": "Malayalam",
        "kn": "Kannada",
        "mr": "Marathi",
        "bn": "Bengali",
        "gu": "Gujarati",
        "pa": "Punjabi",
        "ur": "Urdu"
    }


# ------------------ TEXT TRANSLATION ------------------

@app.post("/translate-text")
def translate_text(data: TextData):
    try:
        translated = GoogleTranslator(
            source="en",
            target=data.target_lang
        ).translate(data.text)

        return {
            "original_text": data.text,
            "translated_text": translated
        }

    except Exception as e:
        return {"error": str(e)}


# ------------------ FILE TRANSLATION ------------------

@app.post("/translate-file")
async def translate_file(file: UploadFile = File(...), target_lang: str = "ta"):
    try:
        content = ""

        if file.filename.endswith(".txt"):
            content = (await file.read()).decode("utf-8")

        elif file.filename.endswith(".pdf"):
            pdf = fitz.open(stream=await file.read(), filetype="pdf")
            for page in pdf:
                content += page.get_text()

        else:
            return {"error": "Only .txt and .pdf supported"}

        translated = GoogleTranslator(
            source="en",
            target=target_lang
        ).translate(content)

        file_like = io.BytesIO(translated.encode("utf-8"))

        return StreamingResponse(
            file_like,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": "attachment; filename=translated_output.txt"
            }
        )

    except Exception as e:
        return {"error": str(e)}
