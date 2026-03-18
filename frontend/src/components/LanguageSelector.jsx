function LanguageSelector({ selectedLanguage, setSelectedLanguage, languages }) {
  return (
    <select
      value={selectedLanguage}
      onChange={(e) => setSelectedLanguage(e.target.value)}
      style={{
        padding: "10px",
        borderRadius: "8px",
        marginBottom: "15px",
        border: "none",
        width: "100%"
      }}
    >
      {languages && languages.map((lang) => (
        <option key={lang} value={lang}>
          {lang}
        </option>
      ))}
    </select>
  );
}

export default LanguageSelector;