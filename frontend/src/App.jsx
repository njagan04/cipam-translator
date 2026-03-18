// ==============================
// IMPORTS
// ==============================

import { useState } from "react";

// Import both translation components
import TextTranslator from "./components/TextTranslator";
import FileTranslation from "./components/Filetranslator";

// Import global styling
import "./App.css";



function App() {

  // ==============================
  // STATE
  // ==============================

  // Controls which mode is visible (text or file)
  const [mode, setMode] = useState("text");



  return (

    <div className="app-container">

      {/* ==============================
         HEADER SECTION
      ============================== */}

      <header className="header">

        <h1>AI Multilingual Translator</h1>

        <p className="tagline">
          ONE NATION, MANY LANGUAGES
        </p>


        {/* Mode Switch Buttons */}

        <div className="mode-buttons">

          <button
            className={mode === "text" ? "active" : ""}
            onClick={() => setMode("text")}
          >
            Text Translation
          </button>

          <button
            className={mode === "file" ? "active" : ""}
            onClick={() => setMode("file")}
          >
            File Translation
          </button>

        </div>

      </header>



      {/* ==============================
         MAIN CONTENT
      ============================== */}

      <main className="main-content">

        <div className="glass-card">

          {/* Switch component based on selected mode */}

          {mode === "text" ? (
            <TextTranslator />
          ) : (
            <FileTranslation />
          )}

        </div>

      </main>

    </div>
  );
}

export default App;