import { useState } from "react";

function DocumentChat({ lang, onClose }) {
  const [messages, setMessages] = useState([
    { role: "assistant", text: `I have analyzed the translated CIPAM document! Feel free to ask me any questions about its content in ${lang}.` }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMsg = input;
    setMessages(prev => [...prev, { role: "user", text: userMsg }]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat-document", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg, lang: lang })
      });
      
      const data = await response.json();
      if (response.ok && data.success) {
        setMessages(prev => [...prev, { role: "assistant", text: data.answer }]);
      } else {
        setMessages(prev => [...prev, { role: "error", text: data.detail || "Failed to get an answer." }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: "error", text: "Network error connecting to RAG backend." }]);
    }
    setLoading(false);
  };

  return (
    <div style={{ marginTop: '20px', padding: '15px', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '12px', background: 'rgba(0,0,0,0.4)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h3 style={{ margin: 0, color: '#4CAF50' }}>💬 RAG File Analysis</h3>
          <button onClick={onClose} className="main-btn" style={{ padding: '5px 10px', fontSize: '12px' }}>Close Chat</button>
      </div>
      
      <div style={{ height: '250px', overflowY: 'auto', marginBottom: '15px', padding: '10px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ textAlign: msg.role === "user" ? "right" : "left" }}>
            <span style={{ 
              display: "inline-block", 
              padding: "10px 14px", 
              borderRadius: "15px",
              backgroundColor: msg.role === "user" ? "var(--primary-color, #007bff)" : (msg.role === "error" ? "#f44336" : "rgba(255,255,255,0.1)"),
              color: "white",
              maxWidth: '80%',
              lineHeight: '1.4'
            }}>
              {msg.text}
            </span>
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: "left" }}>
            <span style={{ display: "inline-block", padding: "10px 14px", borderRadius: "15px", backgroundColor: "rgba(255,255,255,0.1)", color: "#aaa" }}>
               Reflecting on document...
            </span>
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: "10px" }}>
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder={`Ask about the document in ${lang}...`}
          style={{ 
            flex: 1, 
            padding: '12px', 
            borderRadius: '8px', 
            border: '1px solid rgba(255,255,255,0.2)', 
            background: 'rgba(0,0,0,0.3)', 
            color: 'white',
            outline: 'none'
          }}
        />
        <button className="main-btn" onClick={sendMessage} disabled={loading} style={{ minWidth: '80px' }}>
          Send
        </button>
      </div>
    </div>
  );
}

export default DocumentChat;
