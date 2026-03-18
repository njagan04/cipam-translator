import { useState } from "react";
import "./TextTranslator.css";
import TextInput from "./Textinput";
import LanguageSelector from "./LanguageSelector";
import OutputBox from "./OutputBox";

function TextTranslator() {
  const languageList = [
    "Tamil", "Hindi", "Telugu", "Malayalam", "Kannada",
    "Marathi", "Bengali", "Gujarati", "Punjabi", "Urdu"
  ];

  const [inputText, setInputText] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("Tamil");
  const [translatedText, setTranslatedText] = useState("");
  const [statistics, setStatistics] = useState("");
  const [loading, setLoading] = useState(false);

  const handleTranslate = async () => {
    if (!inputText.trim()) {
      alert("Please enter some text to translate.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/translate-text", {
        method: "POST",
        headers: {
          "Accept": "application/json",
        },
        body: new URLSearchParams({
          text: inputText,
          lang: selectedLanguage,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Translation failed");
      }

      const data = await response.json();
      setTranslatedText(data.translated_text);
      setStatistics(data.stats);
    } catch (error) {
      console.error("Translation error:", error);
      alert("Error translating text. Please try again.");
      setTranslatedText("");
      setStatistics("");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setInputText("");
    setTranslatedText("");
    setStatistics("");
  };

  const handleCopy = () => {
    if (!translatedText) {
      alert("No text to copy. Translate something first!");
      return;
    }
    navigator.clipboard.writeText(translatedText);
    alert("Copied to clipboard!");
  };

  const handleSwap = () => {
    const currentIndex = languageList.indexOf(selectedLanguage);
    const nextIndex = (currentIndex + 1) % languageList.length;
    setSelectedLanguage(languageList[nextIndex]);
  };

  return (
    <div className="container">
      <h2>Text Translation</h2>

      <TextInput
        inputText={inputText}
        setInputText={setInputText}
        placeholder="Enter English text here..."
      />

      <LanguageSelector
        selectedLanguage={selectedLanguage}
        setSelectedLanguage={setSelectedLanguage}
        languages={languageList}
      />

      <button className="main-btn" onClick={handleSwap}>
        🔄 Swap Language
      </button>

      <button
        className="main-btn"
        onClick={handleTranslate}
        disabled={!inputText.trim() || loading}
      >
        {loading ? "⏳ Translating..." : "✨ Translate"}
      </button>

      {loading && <div className="spinner"></div>}

      <OutputBox translatedText={translatedText} />

      {statistics && (
        <div className="statistics">
          <p>{statistics}</p>
        </div>
      )}

      <div className="button-group">
        <button className="main-btn clear-btn" onClick={handleClear}>
          Clear
        </button>

        <button
          className="main-btn copy-btn"
          onClick={handleCopy}
          disabled={!translatedText}
        >
          📋 Copy Output
        </button>
      </div>
    </div>
  );
}

export default TextTranslator;