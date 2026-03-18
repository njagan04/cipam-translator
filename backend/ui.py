# ==========================================================
# AI MULTILINGUAL TRANSLATION SYSTEM - FINAL GRADIO VERSION
# ==========================================================

import gradio as gr
from deep_translator import GoogleTranslator
import fitz  # PyMuPDF
import os

# ------------------ LANGUAGE MAP ------------------

languages = {
    "Tamil": "ta",
    "Hindi": "hi",
    "Telugu": "te",
    "Malayalam": "ml",
    "Kannada": "kn",
    "Marathi": "mr",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Urdu": "ur"
}

# ------------------ CHUNK FUNCTION ------------------

def chunk_text(text, max_length=5000):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

# ------------------ SAFE TRANSLATION ------------------

def safe_translate(text, target_lang):
    try:
        if not text.strip():
            return "Please enter some text."

        max_length = 4800  # keep slightly below 5000 for safety
        translated_text = ""

        for i in range(0, len(text), max_length):
            chunk = text[i:i + max_length]

            translated_chunk = GoogleTranslator(
                source="en",
                target=target_lang
            ).translate(chunk)

            translated_text += translated_chunk + " "

        return translated_text.strip()

    except Exception as e:
        return f"Error: {str(e)}"

# ------------------ TEXT TRANSLATION ------------------

def translate_text(text, lang):
    translated = safe_translate(text, languages[lang])
    word_count = len(text.split())
    return translated, f"Word Count: {word_count}"

# ------------------ FILE TRANSLATION ------------------

def translate_file(file, lang):
    try:
        if file is None:
            return "Please upload a file.", None

        content = ""

        # TXT FILE
        if file.name.endswith(".txt"):
            with open(file.name, "r", encoding="utf-8") as f:
                content = f.read()

        # PDF FILE
        elif file.name.endswith(".pdf"):
            pdf = fitz.open(file.name)
            for page in pdf:
                content += page.get_text()

        else:
            return "Only .txt and .pdf files supported.", None

        translated = safe_translate(content, languages[lang])

        # Save translated file
        output_path = "translated_output.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(translated)

        return translated, output_path

    except Exception as e:
        return f"Error: {str(e)}", None


# ==========================================================
# UI DESIGN
# ==========================================================

with gr.Blocks(title="AI Multilingual Translation System") as demo:

    gr.Markdown("## 🌍 AI Multilingual Translation System")
    gr.Markdown("### Translate English Text & Files into Indian Regional Languages")

    # ---------------- TEXT TAB ----------------
    with gr.Tab("Text Translation"):

        text_input = gr.Textbox(
            label="Enter English Text",
            lines=6,
            placeholder="Type or paste English text here..."
        )

        lang_dropdown = gr.Dropdown(
            list(languages.keys()),
            label="Select Target Language"
        )

        translate_btn = gr.Button("Translate")

        text_output = gr.Textbox(
            label="Translated Text",
            lines=6
        )

        word_display = gr.Textbox(
            label="Text Statistics",
            interactive=False
        )

        translate_btn.click(
            translate_text,
            inputs=[text_input, lang_dropdown],
            outputs=[text_output, word_display]
        )

    # ---------------- FILE TAB ----------------
    with gr.Tab("File Translation"):

        file_input = gr.File(label="Upload TXT or PDF File")

        file_lang = gr.Dropdown(
            list(languages.keys()),
            label="Select Target Language"
        )

        file_btn = gr.Button("Translate File")

        file_output = gr.Textbox(
            label="Translated Content",
            lines=10
        )

        download_output = gr.File(label="Download Translated File")

        file_btn.click(
            translate_file,
            inputs=[file_input, file_lang],
            outputs=[file_output, download_output]
        )

# Launch App
demo.launch(debug=True)
