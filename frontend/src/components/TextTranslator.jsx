import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, RefreshCw, Languages, XCircle, CheckCircle2 } from "lucide-react";
import "./TextTranslator.css";

const LANGUAGES = [
  "Tamil", "Hindi", "Telugu", "Malayalam", "Kannada",
  "Marathi", "Bengali", "Gujarati", "Punjabi", "Urdu"
];

function TextTranslator() {
  const [inputText, setInputText] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("Tamil");
  const [translatedText, setTranslatedText] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleTranslate = async () => {
    if (!inputText.trim()) return;

    setLoading(true);
    setTranslatedText("");
    
    try {
      const response = await fetch("http://localhost:8000/translate-text", {
        method: "POST",
        headers: { "Accept": "application/json" },
        body: new URLSearchParams({
          text: inputText,
          lang: selectedLanguage,
          source_lang: "English",
        }),
      });

      if (!response.ok) {
        throw new Error("Translation failed");
      }

      const data = await response.json();
      setTranslatedText(data.translated_text);
    } catch (error) {
      console.error(error);
      alert("Error translating text. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (translatedText) {
      navigator.clipboard.writeText(translatedText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleClear = () => {
    setInputText("");
    setTranslatedText("");
  };

  return (
    <div className="page-container translator-page">
      <div className="translator-header">
        <div className="title-section">
          <h2 className="page-title">Text Translation</h2>
          <p className="page-subtitle">Instantly translate English text to regional languages with structural awareness.</p>
        </div>
      </div>

      <div className="translator-grid">
        {/* Input Region */}
        <div className="panel glass-panel">
          <div className="panel-header">
            <span className="panel-badge">English (Source)</span>
            {inputText && (
              <button className="icon-btn" onClick={handleClear} title="Clear">
                <XCircle size={18} />
              </button>
            )}
          </div>
          <textarea
            className="text-area-input"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type or paste your text here..."
          />
        </div>

        {/* Action Column */}
        <div className="action-column">
          <div className="language-selector-wrapper">
            <Languages size={18} className="lang-icon" />
            <select
              className="lang-select"
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              disabled={loading}
            >
              {LANGUAGES.map((lang) => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
          </div>

          <button
            className="btn-primary translate-btn"
            onClick={handleTranslate}
            disabled={!inputText.trim() || loading}
          >
            {loading ? (
              <><RefreshCw size={18} className="spin-anim" /> Translating...</>
            ) : (
              <>Translate &rarr;</>
            )}
          </button>
        </div>

        {/* Output Region */}
        <div className="panel glass-panel">
          <div className="panel-header">
            <span className="panel-badge highlight-badge">{selectedLanguage} (Target)</span>
            {translatedText && (
              <button className="icon-btn copy-btn" onClick={handleCopy} title="Copy Output">
                {copied ? <CheckCircle2 size={18} className="success-icon" /> : <Copy size={18} />}
              </button>
            )}
          </div>
          
          <div className="text-area-output">
             {translatedText ? (
                <div className="markdown-body">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                  >
                    {translatedText}
                  </ReactMarkdown>
                </div>
             ) : (
                <div className="empty-state">
                  <p>Translation will appear here.</p>
                </div>
             )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TextTranslator;