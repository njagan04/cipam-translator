import { BrowserRouter as Router, Routes, Route, Link, useLocation } from "react-router-dom";
import { Languages, Type, FileText, Home as HomeIcon } from "lucide-react";

import Home from "./pages/Home";
import TextTranslator from "./components/TextTranslator";
import FileTranslation from "./components/Filetranslator";

import "./App.css";

// Navigation Bar Component
function NavBar() {
  const location = useLocation();

  return (
    <nav className="navbar">
      <Link to="/" className="logo-link">
        <span className="logo-header">CIPAM</span>
        <span className="logo-tag">Translator</span>
      </Link>
      
      <div className="nav-links">
        <Link to="/" className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}>
          <HomeIcon size={18} /> Home
        </Link>
        <Link to="/text" className={`nav-item ${location.pathname === '/text' ? 'active' : ''}`}>
          <Type size={18} /> Text Mode
        </Link>
        <Link to="/file" className={`nav-item ${location.pathname === '/file' ? 'active' : ''}`}>
          <FileText size={18} /> File Mode
        </Link>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="app-layout">
        <NavBar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/text" element={<TextTranslator />} />
            <Route path="/file" element={<FileTranslation />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;