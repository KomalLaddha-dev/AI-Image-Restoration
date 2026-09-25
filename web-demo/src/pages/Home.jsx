import React from 'react';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <>
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-badge">
          ✨ AI-Powered Heritage Technology
        </div>

        <h1>Restore History.<br />Discover Heritage.</h1>

        <p className="hero-subtitle">
          Breathe new life into degraded historical photographs with AI restoration,
          and unlock the stories behind the world's greatest monuments.
        </p>

        <div className="cta-grid">
          <Link to="/restore" className="glass-card cta-card" id="cta-restore">
            <div className="cta-icon">🖼️</div>
            <h3>Restore a Photo</h3>
            <p>
              Upload a faded, scratched, or damaged historical photo.
              Our 5-stage AI pipeline will denoise, repair, colorize, and upscale it.
            </p>
            <span className="arrow">→</span>
          </Link>

          <Link to="/identify" className="glass-card cta-card" id="cta-identify">
            <div className="cta-icon">🏛️</div>
            <h3>Identify a Monument</h3>
            <p>
              Snap a photo of any landmark — AI identifies it instantly and
              delivers verified historical facts with source citations.
            </p>
            <span className="arrow">→</span>
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <h2>How It Works</h2>
        <div className="features-grid">
          <div className="glass-card feature-card">
            <div className="feature-icon">🔬</div>
            <h3>5-Stage ML Pipeline</h3>
            <p>
              Old photo repair → denoise → face restore → colorize → upscale.
              Each stage toggleable, using state-of-the-art pretrained models.
            </p>
          </div>

          <div className="glass-card feature-card">
            <div className="feature-icon">🧠</div>
            <h3>Smart Recognition</h3>
            <p>
              MobileNetV3 classifier identifies 50+ monuments from India and
              around the world with 90%+ accuracy.
            </p>
          </div>

          <div className="glass-card feature-card">
            <div className="feature-icon">📚</div>
            <h3>Grounded RAG</h3>
            <p>
              Historical facts retrieved from verified sources (Wikipedia, UNESCO, ASI)
              — never AI-hallucinated. Every fact cited.
            </p>
          </div>

          <div className="glass-card feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Fast & Accessible</h3>
            <p>
              Standard restoration in under 15 seconds. Works on web and mobile.
              No account needed.
            </p>
          </div>
        </div>
      </section>

      {/* Tech Stack Section */}
      <section className="features-section" style={{ paddingTop: 0 }}>
        <h2>Built With</h2>
        <div className="features-grid">
          {[
            { icon: '🐍', name: 'FastAPI', desc: 'Async Python backend' },
            { icon: '🔥', name: 'PyTorch', desc: 'Deep learning inference' },
            { icon: '⚛️', name: 'React', desc: 'Web & mobile frontends' },
            { icon: '🔍', name: 'FAISS', desc: 'Vector similarity search' },
            { icon: '🤖', name: 'Groq + LLama', desc: 'Grounded generation' },
            { icon: '🖼️', name: 'Real-ESRGAN', desc: '4x super-resolution' },
          ].map((tech) => (
            <div key={tech.name} className="glass-card feature-card">
              <div className="feature-icon">{tech.icon}</div>
              <h3>{tech.name}</h3>
              <p>{tech.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
