import { useState } from "react";
import DocumentChat from "./DocumentChat";

function FileTranslation() {
  const [file, setFile] = useState(null);
  const [translatedContent, setTranslatedContent] = useState("");
  const [downloadFile, setDownloadFile] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState("Tamil");
  const [loading, setLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [indexing, setIndexing] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    const filename = selectedFile.name.toLowerCase();
    if (!filename.endsWith(".txt") && !filename.endsWith(".pdf")) {
      alert("Only .txt and .pdf files supported.");
      return;
    }
    setFile(selectedFile);
  };

  const handleTranslate = async () => {
    if (!file) {
      alert("Please upload a file first.");
      return;
    }
    setLoading(true);
    setTranslatedContent("");
    setDownloadFile(null);
    setShowChat(false); // reset chat
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("lang", selectedLanguage);

      const response = await fetch("http://localhost:8000/translate-file", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Translation failed");
      }

      const data = await response.json();
      setTranslatedContent(data.translated_content);
      setDownloadFile(data.download_file);
      
      // Index for RAG
      setIndexing(true);
      fetch("http://localhost:8000/index-document", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: data.translated_content })
      }).then(res => res.json()).then(idxData => {
         if (idxData.success) {
            console.log("Document indexed successfully.");
         }
      }).catch(err => console.error("Indexing failed", err))
      .finally(() => setIndexing(false));

    } catch (error) {
      console.error("Translation error:", error);
      alert("Translation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="file-container">
      <h2 className="title">File Translation</h2>

      <input
        type="file"
        id="fileUpload"
        accept=".txt,.pdf"
        onChange={handleFileChange}
        style={{ display: "none" }}
      />

      <label htmlFor="fileUpload" className="main-btn">
        Choose File
      </label>

      {file && (
        <p className="file-name">
          Selected File: {file.name}
        </p>
      )}

      <select
        className="dropdown"
        value={selectedLanguage}
        onChange={(e) => setSelectedLanguage(e.target.value)}
      >
        <option>Tamil</option>
        <option>Hindi</option>
        <option>Telugu</option>
        <option>Malayalam</option>
        <option>Kannada</option>
        <option>Marathi</option>
        <option>Bengali</option>
        <option>Gujarati</option>
        <option>Punjabi</option>
        <option>Urdu</option>
      </select>

      <button
        className="main-btn"
        onClick={handleTranslate}
        disabled={loading}
      >
        {loading ? "Translating..." : "Translate File"}
      </button>

      <div className="output-box">
        {translatedContent
          ? translatedContent
          : "Translated content will appear here..."}
      </div>

      {downloadFile && downloadFile.url && (
        <a
          href={downloadFile.url}
          target="_blank"
          rel="noopener noreferrer"
          className="main-btn download-btn"
        >
          Download Translated File
        </a>
      )}

      {/* RAG UI Toggle */}
      {translatedContent && !showChat && (
        <button 
           className="main-btn" 
           onClick={() => setShowChat(true)}
           style={{ marginTop: '10px', backgroundColor: '#4CAF50', border: 'none', width: '100%' }}
           disabled={indexing}
        >
           {indexing ? "⏳ Preparing Chat..." : `💬 Chat with Document (in ${selectedLanguage})`}
        </button>
      )}

      {showChat && (
        <DocumentChat lang={selectedLanguage} onClose={() => setShowChat(false)} />
      )}
    </div>
  );
}

export default FileTranslation;