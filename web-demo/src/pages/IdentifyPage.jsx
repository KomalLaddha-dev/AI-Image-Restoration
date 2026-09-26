import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import UploadZone from '../components/UploadZone';
import MonumentCard from '../components/MonumentCard';
import { identifyAndInform } from '../utils/api';
import { motion } from 'motion/react';
import { 
  ArrowCounterClockwise, 
  ArrowRight,
  Scroll,
  WarningCircle,
  Question
} from '@phosphor-icons/react';

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
    <div className="pt-28 pb-20 px-6 max-w-4xl mx-auto min-h-screen">
      <div className="mb-12 text-center md:text-left">
        <h1 className="font-serif text-3xl md:text-5xl font-bold mb-4 text-white">Identify a Monument</h1>
        <p className="text-dark-300 text-lg">Upload a photo of a monument — AI will identify it and show you its history.</p>
      </div>

      {!previewUrl ? (
        <UploadZone
          onFileSelect={handleFileSelect}
          label="Upload a Monument Photo"
        />
      ) : (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          {/* Preview */}
          <div className="glass-card p-4 mb-8">
            <img
              src={previewUrl}
              alt="Uploaded monument"
              className="max-h-[400px] w-auto mx-auto rounded-lg object-contain"
            />
          </div>

          {/* Processing */}
          {isProcessing && (
            <div className="flex flex-col items-center gap-4 py-12">
              <div className="w-8 h-8 rounded-full border-2 border-gold-500/30 border-t-gold-500 animate-spin" />
              <p className="text-dark-300 text-sm">
                Analyzing image... identifying monument...
              </p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="flex items-center gap-3 p-4 mb-8 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              <WarningCircle weight="fill" className="text-xl shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Result */}
          {result && (
            <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
              {result.identification?.recognized ? (
                <>
                  <MonumentCard data={result.identification} />

                  {/* Quick History Summary */}
                  {result.history && (
                    <div className="glass-card p-8 mt-6">
                      <h3 className="font-serif text-2xl font-bold mb-4 text-gold-500 flex items-center gap-2">
                        <Scroll weight="duotone" />
                        Historical Summary
                      </h3>
                      <p className="text-sm leading-relaxed text-dark-300 mb-6">
                        {result.history.summary}
                      </p>

                      {result.history.sources?.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-white/5">
                          <p className="text-xs text-dark-400 mb-3 uppercase tracking-wider font-semibold">
                            Sources
                          </p>
                          <ul className="space-y-2">
                            {result.history.sources.map((s, i) => (
                              <li key={i} className="text-sm">
                                {s.url ? (
                                  <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-gold-500 hover:text-gold-400 transition-colors">
                                    {s.name}
                                  </a>
                                ) : (
                                  <span className="text-dark-300">{s.name}</span>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <button
                        onClick={() => navigate(`/history/${result.identification.monument_id}`)}
                        className="btn-primary mt-8 w-full sm:w-auto"
                      >
                        View Full History <ArrowRight weight="bold" />
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <div className="glass-card p-12 text-center flex flex-col items-center">
                  <Question weight="duotone" className="text-6xl text-gold-500/50 mb-4" />
                  <h3 className="text-2xl font-bold mb-2 text-white">Not Recognized</h3>
                  <p className="text-dark-300 text-sm">
                    {result.identification?.message || "This monument isn't in our database yet."}
                  </p>
                </div>
              )}
            </motion.div>
          )}

          {/* Reset button */}
          {!isProcessing && (
            <div className="text-center mt-8">
              <button onClick={handleReset} className="btn-secondary w-full sm:w-auto">
                <ArrowCounterClockwise weight="bold" />
                Try Another Photo
              </button>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
