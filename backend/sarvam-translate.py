# ==========================================================
# AI MULTILINGUAL TRANSLATION SYSTEM - SARVAM AI VERSION
# ==========================================================

import gradio as gr
from sarvamai import SarvamAI
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
# ------------------ API CONFIG ------------------

# 🔐 Recommended: Use environment variable instead of hardcoding
# export SARVAM_API_KEY=your_key   (Mac/Linux)
# setx SARVAM_API_KEY your_key     (Windows)

client = SarvamAI(
    api_subscription_key=os.getenv("KEY")
)

# ------------------ LANGUAGE MAP ------------------

languages = {
    "Hindi": "hi-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Kannada": "kn-IN",
    "Malayalam": "ml-IN",
    "Marathi": "mr-IN",
    "Gujarati": "gu-IN",
    "Punjabi": "pa-IN",
    "Bengali": "bn-IN"
}

# ------------------ TRANSLATION FUNCTION ------------------

def translate_text(text, lang, tone, numerals, gender):
    try:
        if not text.strip():
            return "Please enter some text."

        response = client.text.translate(
            input=text,
            source_language_code="en-IN",
            target_language_code=languages[lang],
            speaker_gender=gender,
            mode=tone,
            model="mayura:v1",
            numerals_format=numerals
        )

        return response.translated_text  # ✅ only show translated text

    except Exception as e:
        return f"Error: {str(e)}"

# ==========================================================
# UI DESIGN
# ==========================================================

with gr.Blocks(title="AI Multilingual Translation System - Sarvam AI") as demo:

    gr.Markdown("## 🇮🇳 AI Multilingual Translation System")
    gr.Markdown("### Powered by Sarvam AI")

    text_input = gr.Textbox(
        label="Enter Text",
        lines=8,
        placeholder="Type your text here..."
    )

    language_dropdown = gr.Dropdown(
        list(languages.keys()),
        label="Select Target Language",
        value="Hindi"
    )

    tone_dropdown = gr.Dropdown(
        ["formal", "modern-colloquial", "classical-colloquial", "code-mixed"],
        label="Select Tone",
        value="formal"
    )

    numeral_dropdown = gr.Dropdown(
        ["native", "international"],
        label="Numeral Format",
        value="international"
    )

    gender_dropdown = gr.Dropdown(
        ["Male", "Female"],
        label="Speaker Gender",
        value="Male"
    )

    translate_button = gr.Button("Translate")

    output_box = gr.Textbox(
        label="Translated Output",
        lines=10
    )

    translate_button.click(
        translate_text,
        inputs=[
            text_input,
            language_dropdown,
            tone_dropdown,
            numeral_dropdown,
            gender_dropdown
        ],
        outputs=output_box
    )

demo.launch()
