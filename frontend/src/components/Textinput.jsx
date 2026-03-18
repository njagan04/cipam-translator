function TextInput({ inputText, setInputText }) {
  return (
    <textarea
      value={inputText}
      onChange={(e) => setInputText(e.target.value)}
      placeholder="Enter text here..."
      rows="5"
      style={{
        width: "93%",
        padding: "14px",
        borderRadius: "10px",
        border: "none",
        outline: "none",
        marginBottom: "15px",
        fontSize: "15px",
        background: "rgba(255,255,255,0.08)",
        color: "white"
      }}
    />
  );
}

export default TextInput;