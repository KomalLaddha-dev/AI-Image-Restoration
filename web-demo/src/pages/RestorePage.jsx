import React, { useState, useCallback } from 'react';
import UploadZone from '../components/UploadZone';
import BeforeAfterSlider from '../components/BeforeAfterSlider';
import ProgressBar from '../components/ProgressBar';
import { restoreSync } from '../utils/api';
import { motion } from 'motion/react';
import { 
  Waves, 
  UserFocus, 
  Palette, 
  DownloadSimple, 
  ArrowCounterClockwise,
  Sparkle,
  X,
  WarningCircle,
  CheckCircle
} from '@phosphor-icons/react';

const STAGES = [
  { key: 'denoise', label: 'Denoise', icon: <Waves weight="duotone" className="mr-2" />, default: false },
  { key: 'face_restore', label: 'Face Restore', icon: <UserFocus weight="duotone" className="mr-2" />, default: false },
  { key: 'colorize', label: 'Colorize', icon: <Palette weight="duotone" className="mr-2" />, default: false },
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
    <div className="pt-28 pb-20 px-6 max-w-4xl mx-auto min-h-screen">
      <div className="mb-12 text-center md:text-left">
        <h1 className="font-serif text-3xl md:text-5xl font-bold mb-4 text-white">Restore a Photo</h1>
        <p className="text-dark-300 text-lg">Upload a degraded historical photo — our AI pipeline will restore it.</p>
      </div>

      {!originalUrl ? (
        <UploadZone
          onFileSelect={handleFileSelect}
          label="Upload a Historical Photo"
        />
      ) : (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          {/* Stage Toggles */}
          {!restoredUrl && (
            <div className="mb-8">
              <p className="text-sm text-dark-300 mb-4 font-medium uppercase tracking-wider">
                Select restoration stages
              </p>
              <div className="flex flex-wrap gap-3">
                {STAGES.map(stage => {
                  const isActive = stages.includes(stage.key);
                  return (
                    <button
                      key={stage.key}
                      onClick={() => toggleStage(stage.key)}
                      disabled={isProcessing}
                      className={`flex items-center px-4 py-2.5 rounded-xl border text-sm font-medium transition-all duration-200 ease-out 
                        ${isActive 
                          ? 'border-gold-500/50 bg-gold-500/10 text-gold-400 shadow-[0_0_15px_rgba(212,168,83,0.15)]' 
                          : 'border-white/10 bg-white/5 text-dark-300 hover:border-white/20 hover:bg-white/10'
                        }
                      `}
                    >
                      {stage.icon}
                      {stage.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Processing state */}
          {isProcessing && (
            <div className="mb-8">
              <ProgressBar progress={progress} label="Restoring image..." />
              <div className="flex items-center gap-3 mt-4">
                <div className="w-5 h-5 rounded-full border-2 border-gold-500/30 border-t-gold-500 animate-spin" />
                <span className="text-sm text-dark-300">
                  Running pipeline (BOPBTL + Upscale + {stages.length} optional stages)...
                </span>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="flex items-center gap-3 p-4 mb-8 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              <WarningCircle weight="fill" className="text-xl shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Before/After comparison */}
          {restoredUrl ? (
            <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
              <BeforeAfterSlider
                beforeSrc={originalUrl}
                afterSrc={restoredUrl}
              />

              {result && (
                <div className="glass-card p-6 mt-8 text-center border-gold-500/20 bg-gold-500/5">
                  <div className="flex items-center justify-center gap-2 text-gold-400 font-semibold mb-2">
                    <CheckCircle weight="fill" className="text-xl" />
                    <span>Restored in {result.processingTime}ms</span>
                  </div>
                  <p className="text-sm text-dark-300">
                    Stages applied: <span className="text-white/80">{result.stages.join(' → ')}</span>
                  </p>
                </div>
              )}

              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-8">
                <a href={restoredUrl} download="restored.png" className="btn-primary w-full sm:w-auto">
                  <DownloadSimple weight="bold" className="text-lg" />
                  Download Restored
                </a>
                <button onClick={handleReset} className="btn-secondary w-full sm:w-auto">
                  <ArrowCounterClockwise weight="bold" className="text-lg" />
                  Restore Another
                </button>
              </div>
            </motion.div>
          ) : (
            <div>
              {/* Preview original */}
              <div className="glass-card p-4 mb-8">
                <img
                  src={originalUrl}
                  alt="Original"
                  className="max-h-[500px] w-auto mx-auto rounded-lg object-contain"
                />
                <div className="text-center mt-4 text-sm text-dark-400">
                  <span className="font-medium text-dark-200">{originalFile?.name}</span>
                  <span className="mx-2">•</span>
                  <span>{(originalFile?.size / 1024).toFixed(0)} KB</span>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-center gap-4">
                <button
                  onClick={handleRestore}
                  className="btn-primary flex-1 w-full"
                  disabled={isProcessing}
                >
                  <Sparkle weight="fill" className={isProcessing ? 'animate-pulse' : ''} />
                  {isProcessing ? 'Processing...' : 'Restore Image'}
                </button>
                <button onClick={handleReset} className="btn-secondary sm:w-auto w-full">
                  <X weight="bold" />
                  Cancel
                </button>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
