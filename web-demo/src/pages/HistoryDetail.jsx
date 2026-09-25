import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getHistory } from '../utils/api';

export default function HistoryDetail() {
  const { id } = useParams();
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const data = await getHistory(id);
        setHistory(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [id]);

  if (loading) {
    return (
      <div className="page" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <div className="spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div style={{
          padding: 'var(--space-8)',
          textAlign: 'center',
          color: 'var(--color-error)',
        }}>
          <p>Failed to load history: {error}</p>
          <Link to="/identify" className="btn btn-secondary" style={{ marginTop: 'var(--space-4)' }}>
            ← Back to Identify
          </Link>
        </div>
      </div>
    );
  }

  if (!history) return null;

  return (
    <div className="page">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-10)' }}>
        <Link to="/identify" style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--color-text-muted)',
          marginBottom: 'var(--space-4)',
          display: 'inline-block',
        }}>
          ← Back to Identify
        </Link>

        <h1 style={{
          fontFamily: 'var(--font-serif)',
          fontSize: 'clamp(2rem, 5vw, 3.5rem)',
          background: 'var(--color-accent-gradient)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          marginBottom: 'var(--space-4)',
        }}>
          {history.name}
        </h1>

        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 'var(--space-6)',
          color: 'var(--color-text-secondary)',
          fontSize: 'var(--text-sm)',
        }}>
          {history.location && <span>📍 {history.location}</span>}
          {history.era && <span>🕐 {history.era}</span>}
          {history.builder && <span>🏗️ {history.builder}</span>}
          {history.architectural_style && <span>🏛️ {history.architectural_style}</span>}
          {history.unesco_status && (
            <span style={{ color: 'var(--color-accent-gold)' }}>
              🏆 {history.unesco_status}
            </span>
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="glass-card" style={{ padding: 'var(--space-8)', marginBottom: 'var(--space-8)' }}>
        <h2 style={{
          fontFamily: 'var(--font-serif)',
          fontSize: 'var(--text-2xl)',
          marginBottom: 'var(--space-4)',
        }}>
          Historical Summary
        </h2>
        <div style={{
          fontSize: 'var(--text-base)',
          lineHeight: 1.8,
          color: 'var(--color-text-secondary)',
          whiteSpace: 'pre-wrap',
        }}>
          {history.summary}
        </div>
      </div>

      {/* Timeline */}
      {history.timeline?.length > 0 && (
        <div className="glass-card" style={{ padding: 'var(--space-8)', marginBottom: 'var(--space-8)' }}>
          <h2 style={{
            fontFamily: 'var(--font-serif)',
            fontSize: 'var(--text-2xl)',
            marginBottom: 'var(--space-6)',
          }}>
            Timeline
          </h2>
          <div className="timeline">
            {history.timeline.map((event, i) => (
              <div key={i} className="timeline-event">
                <div className="year">{event.year}</div>
                <div className="event-text">{event.event}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sources */}
      {history.sources?.length > 0 && (
        <div className="glass-card" style={{ padding: 'var(--space-8)' }}>
          <h2 style={{
            fontFamily: 'var(--font-serif)',
            fontSize: 'var(--text-2xl)',
            marginBottom: 'var(--space-4)',
          }}>
            Sources
          </h2>
          <ul className="sources-list">
            {history.sources.map((source, i) => (
              <li key={i}>
                📄{' '}
                {source.url ? (
                  <a href={source.url} target="_blank" rel="noopener noreferrer">
                    {source.name}
                  </a>
                ) : (
                  source.name
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
