function OutputBox({ translatedText }) {
  return (
    <div className="output-box">
      {translatedText || "Translation will appear here..."}
    </div>
  );
}

export default OutputBox;