import { Link } from "react-router-dom";
import { FileText, Type } from "lucide-react";
import "./Home.css";

function Home() {
  return (
    <div className="home-container page-container">
      <div className="hero-section">
        <div className="hero-badge">Cell for IPR Promotion and Management</div>
        <h1 className="hero-title">
          Bridging the Language Divide in <span className="highlight-text">Indian IP</span>
        </h1>
        <p className="hero-description">
          The CIPAM translation engine empowers innovators across the nation by breaking down language barriers. Translate Intellectual Property documents into 10+ regional languages securely and instantly, preserving native formatting and structural integrity.
        </p>
      </div>

      <div className="mode-cards">
        <Link to="/text" className="mode-card glass-panel">
          <div className="card-icon-wrapper primary-glow">
            <Type className="card-icon" />
          </div>
          <h2 className="card-title">Text Translation</h2>
          <p className="card-description">
            Instantly translate raw paragraphs, patents claims, and descriptions into any supported Indian regional language.
          </p>
          <div className="card-action">Start Translation &rarr;</div>
        </Link>

        <Link to="/file" className="mode-card glass-panel">
          <div className="card-icon-wrapper secondary-glow">
            <FileText className="card-icon" />
          </div>
          <h2 className="card-title">Document Translation</h2>
          <p className="card-description">
            Upload PDFs or TXT files. Preserve structural layout while translating. Includes intelligent RAG for querying your documents.
          </p>
          <div className="card-action">Upload Document &rarr;</div>
        </Link>
      </div>
      
      <div className="info-section glass-panel">
        <h3 className="info-title">Why CIPAM Translation?</h3>
        <ul className="info-list">
          <li><strong>Context-Aware:</strong> Specially trained on legal and IP terminologies.</li>
          <li><strong>Layout Preservation:</strong> Ensures uploaded documents retain their original form.</li>
          <li><strong>Document Intelligence:</strong> Ask interactive questions directly to your translated files.</li>
        </ul>
      </div>
    </div>
  );
}

export default Home;
