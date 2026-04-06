import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { UploadCloud, File, Download, Search, Send, RefreshCw, MessageSquare } from "lucide-react";
import html2pdf from "html2pdf.js";
import "./Filetranslator.css";

const LANGUAGES = [
  "Tamil", "Hindi", "Telugu", "Malayalam", "Kannada",
  "Marathi", "Bengali", "Gujarati", "Punjabi", "Urdu"
];

function FileTranslation() {
  const [file, setFile] = useState(null);
  const [translatedContent, setTranslatedContent] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("Tamil");
  const [loading, setLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // RAG Chat State
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, chatLoading]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    
    // Check extension
    const filename = selectedFile.name.toLowerCase();
    if (!filename.endsWith(".txt") && !filename.endsWith(".pdf")) {
      alert("Only .txt and .pdf files supported.");
      return;
    }
    
    // Check file size (10MB maximum limit)
    if (selectedFile.size > 10 * 1024 * 1024) {
      alert("File size exceeds the 10MB limit. Please upload a smaller document.");
      return;
    }
    
    setFile(selectedFile);
    setTranslatedContent("");
    setChatMessages([]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const selectedFile = e.dataTransfer.files[0];
      
      const filename = selectedFile.name.toLowerCase();
      if (!filename.endsWith(".txt") && !filename.endsWith(".pdf")) {
        alert("Only .txt and .pdf files supported.");
        return;
      }
      
      // Check file size (10MB maximum limit)
      if (selectedFile.size > 10 * 1024 * 1024) {
        alert("File size exceeds the 10MB limit. Please upload a smaller document.");
        return;
      }
      
      setFile(selectedFile);
      setTranslatedContent("");
      setChatMessages([]);
    }
  };

  const handleTranslate = async () => {
    if (!file) {
      alert("Please upload a file first.");
      return;
    }
    setLoading(true);
    setTranslatedContent("");
    setChatMessages([]);
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("lang", selectedLanguage);

      const response = await fetch("http://localhost:8000/translate-file", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Translation failed");
      }

      const data = await response.json();
      setTranslatedContent(data.translated_content);
      
      // Index for RAG
      setIndexing(true);
      setChatMessages([
        { role: "assistant", text: `I am analyzing the translated document. Please wait...` }
      ]);
      
      const idxRes = await fetch("http://localhost:8000/index-document", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: data.translated_content })
      });
      const idxData = await idxRes.json();
      
      if (idxData.success) {
         setChatMessages([
           { role: "assistant", text: `I have analyzed the translated CIPAM document! Feel free to ask me any questions about its content in ${selectedLanguage}.` }
         ]);
      } else {
         throw new Error("Indexing failed");
      }

    } catch (error) {
      console.error("Translation error:", error);
      alert("Process failed. Please try again.");
    } finally {
      setLoading(false);
      setIndexing(false);
    }
  };

  const handleDownload = () => {
    const mdContainer = document.querySelector('.markdown-body');
    if (!mdContainer) return;
    
    const rawHtml = mdContainer.innerHTML;
    const fullHtml = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Translated Document (${selectedLanguage})</title>
        <style>
          body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            line-height: 1.6; color: #24292e; max-width: 900px; margin: 0 auto; padding: 40px; 
          }
          h1, h2, h3, h4 { border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; margin-top: 24px; margin-bottom: 16px; color: #000; }
          table { border-collapse: collapse; width: 100%; margin: 16px 0; }
          table th, table td { padding: 6px 13px; border: 1px solid #dfe2e5; }
          table tr:nth-child(2n) { background-color: #f6f8fa; }
        </style>
      </head>
      <body>
        ${rawHtml}
      </body>
      </html>
    `;
    
    // Natively package into a flawlessly offline-readable HTML document for exact styling
    const blob = new Blob([fullHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement("a");
    a.href = url;
    a.download = `translated_${file?.name?.replace(/\.[^/.]+$/, "") || 'document'}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const sendMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMsg = chatInput;
    setChatMessages(prev => [...prev, { role: "user", text: userMsg }]);
    setChatInput("");
    setChatLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat-document", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg, lang: selectedLanguage })
      });
      
      const data = await response.json();
      if (response.ok && data.success) {
        setChatMessages(prev => [...prev, { role: "assistant", text: data.answer }]);
      } else {
        setChatMessages(prev => [...prev, { role: "error", text: data.detail || "Failed to get an answer." }]);
      }
    } catch (e) {
      setChatMessages(prev => [...prev, { role: "error", text: "Network error connecting to RAG backend." }]);
    }
    setChatLoading(false);
  };

  return (
    <div className="page-container file-page">
      <div className="file-header">
        <h2 className="page-title">Document Translation</h2>
        <p className="page-subtitle">Upload your IP files to translate and chat with the localized content.</p>
      </div>

      <div className="file-workspace glass-panel">
        
        {/* Left Sidebar: Controls & Upload */}
        <div className="upload-sidebar">
          <input
            type="file"
            accept=".txt,.pdf"
            onChange={handleFileChange}
            style={{ display: "none" }}
            ref={fileInputRef}
          />

          <div 
            className={`upload-zone ${isDragging ? "active" : ""}`} 
            onClick={() => fileInputRef.current.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            style={{
              borderColor: isDragging ? "var(--primary-color)" : "",
              background: isDragging ? "rgba(79, 70, 229, 0.1)" : ""
            }}
          >
            <UploadCloud size={40} className="upload-icon" />
            <h3 style={{ marginBottom: "8px" }}>Upload Document</h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Drag & Drop or Click to Browse</p>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>Max size: 10MB (.pdf, .txt)</p>
          </div>

          {file && (
            <div className="file-name-display">
              <File size={16} /> 
              {file.name}
            </div>
          )}

          <div className="settings-group">
            <span className="settings-label">Target Language</span>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              disabled={loading}
            >
              {LANGUAGES.map(lang => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
          </div>

          <button
            className="btn-primary"
            onClick={handleTranslate}
            disabled={loading || !file}
            style={{ marginTop: "1rem" }}
          >
            {loading ? <><RefreshCw size={18} className="spin-anim" /> Processing...</> : "Translate Document"}
          </button>
        </div>

        {/* Center: Document Viewer */}
        <div className="document-pane">
          <div className="pane-header">
            <span className="pane-title">
              <FileText size={18} /> Translated Output
            </span>
          </div>

          <div className={`document-content ${!translatedContent ? 'empty' : ''}`}>
            {translatedContent ? (
              <>
                <div className="markdown-body">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                  >
                    {translatedContent}
                  </ReactMarkdown>
                </div>
                <button 
                  onClick={handleDownload} 
                  className="floating-download-btn"
                >
                  <Download size={18} /> Download HTML
                </button>
              </>
            ) : (
              <>
                <File size={48} style={{ opacity: 0.3 }} />
                <p>Upload and translate a document to view it here.</p>
              </>
            )}
          </div>
        </div>

        {/* Right: RAG Chat */}
        <div className="chat-pane">
          <div className="chat-header">
            <span className="pane-title"><MessageSquare size={18} /> RAG Assistant</span>
            {indexing && <span style={{ fontSize: '0.75rem', color: 'var(--primary-color)' }}>Indexing...</span>}
          </div>
          
          <div className="chat-messages">
            {chatMessages.length === 0 && !translatedContent && (
               <div style={{ textAlign: "center", color: "var(--text-muted)", marginTop: "2rem", fontSize: "0.9rem" }}>
                 Chat interface will activate after translation.
               </div>
            )}
            
            {chatMessages.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.role}`}>
                {msg.role === 'assistant' ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.text}
                  </ReactMarkdown>
                ) : (
                  msg.text
                )}
              </div>
            ))}
            
            {chatLoading && (
              <div className="chat-bubble assistant" style={{ fontStyle: "italic", opacity: 0.7 }}>
                Thinking...
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="chat-input-area">
            <input 
              type="text" 
              className="chat-input"
              value={chatInput} 
              onChange={(e) => setChatInput(e.target.value)} 
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask a question..."
              disabled={indexing || chatMessages.length === 0 || !translatedContent}
            />
            <button 
              className="send-btn" 
              onClick={sendMessage} 
              disabled={chatLoading || indexing || !chatInput.trim()}
            >
              <Send size={16} />
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

// Ensure lucide icon FileText is imported
import { FileText } from "lucide-react";

export default FileTranslation;