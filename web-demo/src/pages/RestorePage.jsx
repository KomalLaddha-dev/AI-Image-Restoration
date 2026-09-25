import React, { useState, useCallback } from 'react';
import UploadZone from '../components/UploadZone';
import BeforeAfterSlider from '../components/BeforeAfterSlider';
import ProgressBar from '../components/ProgressBar';
import { restoreSync } from '../utils/api';

const STAGES = [
  { key: 'denoise', label: '🔇 Denoise', default: false },
  { key: 'face_restore', label: '👤 Face Restore', default: false },
  { key: 'colorize', label: '🎨 Colorize', default: false },
];

export default function RestorePage() {
  const [originalFile, setOriginalFile] = useState(null);
  const [originalUrl, setOriginalUrl] = useState(null);
  const [restoredUrl, setRestoredUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stages, setStages] = useState(
    STAGES.filter(s => s.default).map(s => s.key)
  );
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const toggleStage = (key) => {
    setStages(prev =>
      prev.includes(key) ? prev.filter(s => s !== key) : [...prev, key]
    );
  };

  const handleFileSelect = useCallback((file) => {
    setOriginalFile(file);
    setOriginalUrl(URL.createObjectURL(file));
    setRestoredUrl(null);
    setResult(null);
    setError(null);
  }, []);

  const handleRestore = async () => {
    if (!originalFile) return;

    setIsProcessing(true);
    setProgress(10);
    setError(null);

    try {
      // Simulate stage progress
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 8, 90));
      }, 500);

      const options = {
        face_restore: stages.includes('face_restore'),
        colorize: stages.includes('colorize'),
        denoise: stages.includes('denoise'),
        mode: 'standard'
      };

      const data = await restoreSync(originalFile, options);

      clearInterval(progressInterval);
      setProgress(100);
      setRestoredUrl(data.url);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Restoration failed. Is the backend running?');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setOriginalFile(null);
    setOriginalUrl(null);
    setRestoredUrl(null);
    setResult(null);
    setError(null);
    setProgress(0);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Restore a Photo</h1>
        <p>Upload a degraded historical photo — our AI pipeline will restore it.</p>
      </div>

      {!originalUrl ? (
        <UploadZone
          onFileSelect={handleFileSelect}
          label="Upload a Historical Photo"
        />
      ) : (
        <div>
          {/* Stage Toggles */}
          {!restoredUrl && (
            <div style={{ marginBottom: 'var(--space-6)' }}>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-3)' }}>
                Select restoration stages:
              </p>
              <div className="stage-toggles">
                {STAGES.map(stage => (
                  <button
                    key={stage.key}
                    className={`stage-toggle ${stages.includes(stage.key) ? 'active' : ''}`}
                    onClick={() => toggleStage(stage.key)}
                    disabled={isProcessing}
                  >
                    {stage.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Processing state */}
          {isProcessing && (
            <div style={{ marginBottom: 'var(--space-6)' }}>
              <ProgressBar progress={progress} label="Restoring image..." />
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginTop: 'var(--space-3)' }}>
                <div className="spinner" />
                <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>
                  Running pipeline (BOPBTL + Upscale + {stages.length} optional stages)...
                </span>
              </div>
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

          {/* Before/After comparison */}
          {restoredUrl ? (
            <div>
              <BeforeAfterSlider
                beforeSrc={originalUrl}
                afterSrc={restoredUrl}
              />

              {result && (
                <div className="glass-card" style={{
                  padding: 'var(--space-6)',
                  marginTop: 'var(--space-6)',
                  textAlign: 'center',
                }}>
                  <p style={{ color: 'var(--color-accent-gold)', fontWeight: 600 }}>
                    ✨ Restored in {result.processingTime}ms
                  </p>
                  <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-2)' }}>
                    Stages applied: {result.stages.join(' → ')}
                  </p>
                </div>
              )}

              <div style={{ display: 'flex', gap: 'var(--space-4)', marginTop: 'var(--space-6)', justifyContent: 'center' }}>
                <a href={restoredUrl} download="restored.png" className="btn btn-primary">
                  💾 Download Restored
                </a>
                <button onClick={handleReset} className="btn btn-secondary">
                  🔄 Restore Another
                </button>
              </div>
            </div>
          ) : (
            <div>
              {/* Preview original */}
              <div className="glass-card" style={{
                padding: 'var(--space-4)',
                marginBottom: 'var(--space-6)',
                textAlign: 'center',
              }}>
                <img
                  src={originalUrl}
                  alt="Original"
                  style={{
                    maxHeight: '400px',
                    borderRadius: 'var(--radius-lg)',
                    margin: '0 auto',
                  }}
                />
                <p style={{
                  fontSize: 'var(--text-sm)',
                  color: 'var(--color-text-muted)',
                  marginTop: 'var(--space-3)',
                }}>
                  {originalFile?.name} — {(originalFile?.size / 1024).toFixed(0)} KB
                </p>
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-4)', justifyContent: 'center' }}>
                <button
                  onClick={handleRestore}
                  className="btn btn-primary"
                  disabled={isProcessing}
                >
                  {isProcessing ? 'Processing...' : '✨ Restore Image'}
                </button>
                <button onClick={handleReset} className="btn btn-secondary">
                  ✕ Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
