import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import UploadZone from '../components/UploadZone';
import MonumentCard from '../components/MonumentCard';
import { identifyAndInform } from '../utils/api';

export default function IdentifyPage() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleFileSelect = useCallback(async (file) => {
    setPreviewUrl(URL.createObjectURL(file));
    setIsProcessing(true);
    setError(null);
    setResult(null);

    try {
      const data = await identifyAndInform(file);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Identification failed. Is the backend running?');
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const handleReset = () => {
    setResult(null);
    setPreviewUrl(null);
    setError(null);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Identify a Monument</h1>
        <p>Upload a photo of a monument — AI will identify it and show you its history.</p>
      </div>

      {!previewUrl ? (
        <UploadZone
          onFileSelect={handleFileSelect}
          label="Upload a Monument Photo"
        />
      ) : (
        <div>
          {/* Preview */}
          <div className="glass-card" style={{
            padding: 'var(--space-4)',
            marginBottom: 'var(--space-6)',
            textAlign: 'center',
          }}>
            <img
              src={previewUrl}
              alt="Uploaded monument"
              style={{
                maxHeight: '350px',
                borderRadius: 'var(--radius-lg)',
                margin: '0 auto',
              }}
            />
          </div>

          {/* Processing */}
          {isProcessing && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 'var(--space-4)',
              padding: 'var(--space-8)',
            }}>
              <div className="spinner" />
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
                Analyzing image... identifying monument...
              </p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div style={{
              padding: 'var(--space-4)',
              background: 'rgba(248, 113, 113, 0.1)',
              border: '1px solid rgba(248, 113, 113, 0.3)',
              borderRadius: 'var(--radius-lg)',
              color: 'var(--color-error)',
              fontSize: 'var(--text-sm)',
              marginBottom: 'var(--space-6)',
            }}>
              ⚠️ {error}
            </div>
          )}

          {/* Result */}
          {result && (
            <div>
              {result.identification?.recognized ? (
                <>
                  <MonumentCard data={result.identification} />

                  {/* Quick History Summary */}
                  {result.history && (
                    <div className="glass-card" style={{ padding: 'var(--space-6)', marginTop: 'var(--space-6)' }}>
                      <h3 style={{
                        fontFamily: 'var(--font-serif)',
                        fontSize: 'var(--text-xl)',
                        marginBottom: 'var(--space-4)',
                        color: 'var(--color-accent-gold)',
                      }}>
                        📜 Historical Summary
                      </h3>
                      <p style={{
                        fontSize: 'var(--text-sm)',
                        lineHeight: 1.8,
                        color: 'var(--color-text-secondary)',
                      }}>
                        {result.history.summary}
                      </p>

                      {result.history.sources?.length > 0 && (
                        <div style={{ marginTop: 'var(--space-4)' }}>
                          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-2)' }}>
                            Sources:
                          </p>
                          <ul className="sources-list">
                            {result.history.sources.map((s, i) => (
                              <li key={i}>
                                {s.url ? (
                                  <a href={s.url} target="_blank" rel="noopener noreferrer">{s.name}</a>
                                ) : (
                                  s.name
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <button
                        onClick={() => navigate(`/history/${result.identification.monument_id}`)}
                        className="btn btn-primary"
                        style={{ marginTop: 'var(--space-6)' }}
                      >
                        View Full History →
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <div className="glass-card" style={{
                  padding: 'var(--space-8)',
                  textAlign: 'center',
                }}>
                  <div style={{ fontSize: '3rem', marginBottom: 'var(--space-4)' }}>🤔</div>
                  <h3 style={{ marginBottom: 'var(--space-2)' }}>Not Recognized</h3>
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
                    {result.identification?.message || "This monument isn't in our database yet."}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Reset button */}
          {!isProcessing && (
            <div style={{ textAlign: 'center', marginTop: 'var(--space-6)' }}>
              <button onClick={handleReset} className="btn btn-secondary">
                🔄 Try Another Photo
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
