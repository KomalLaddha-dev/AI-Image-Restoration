import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import UploadZone from '../components/UploadZone';
import BeforeAfterSlider from '../components/BeforeAfterSlider';
import ProgressBar from '../components/ProgressBar';
import { restoreSync } from '../utils/api';
import { MagicWand, ImageSquare, DownloadSimple, Faders, Sparkle, CameraRotate, DropHalfBottom } from '@phosphor-icons/react';

export default function RestorePage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [options, setOptions] = useState({
    denoise: true,
    colorize: false,
    upscale: false,
    scratch_repair: false,
  });

  const handleToggle = (key) => {
    setOptions(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleRestore = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setProgress(0);
    setResult(null);

    // Simulate progress animation since actual API might block
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 5, 90));
    }, 500);

    try {
      const resultData = await restoreSync(file, options);
      setResult(resultData.url);
      setProgress(100);
    } catch (err) {
      setError(err.message || 'An error occurred during restoration');
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full min-h-screen py-32 px-6 md:px-12 max-w-7xl mx-auto flex flex-col relative z-10"
    >
      <div className="text-center mb-16">
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="font-serif text-4xl md:text-6xl font-bold text-white mb-4 tracking-tight"
        >
          Photo <span className="italic text-gold-400 font-light">Restoration</span>
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-dark-300 max-w-xl mx-auto text-lg font-light"
        >
          Our advanced AI pipeline reconstructs lost details, removes noise, and injects historically accurate color into degraded photographs.
        </motion.p>
      </div>

      {!result && !loading && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-3xl mx-auto"
        >
          <UploadZone onFileSelect={setFile} file={file} />
          
          <AnimatePresence>
            {file && (
              <motion.div 
                initial={{ opacity: 0, height: 0, mt: 0 }}
                animate={{ opacity: 1, height: 'auto', mt: 32 }}
                exit={{ opacity: 0, height: 0, mt: 0 }}
                className="glass-card p-8 bg-black/40 border border-white/10"
              >
                <div className="flex items-center gap-3 mb-6 border-b border-white/10 pb-4">
                  <Faders weight="duotone" className="text-gold-500 text-2xl" />
                  <h3 className="font-serif text-xl font-bold text-white tracking-wide">Pipeline Configuration</h3>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                  <ToggleOption 
                    icon={<CameraRotate weight="duotone" />}
                    title="Denoise & Deblur"
                    desc="Removes film grain, compression artifacts, and motion blur using NAFNet."
                    active={options.denoise}
                    onClick={() => handleToggle('denoise')}
                  />
                  <ToggleOption 
                    icon={<DropHalfBottom weight="duotone" />}
                    title="Colorize (DDColor)"
                    desc="Injects historically accurate color into grayscale or sepia photographs."
                    active={options.colorize}
                    onClick={() => handleToggle('colorize')}
                  />
                  <ToggleOption 
                    icon={<ImageSquare weight="duotone" />}
                    title="Upscale (Real-ESRGAN)"
                    desc="Increases resolution and reconstructs fine details like textures and edges."
                    active={options.upscale}
                    onClick={() => handleToggle('upscale')}
                  />
                  <ToggleOption 
                    icon={<Sparkle weight="duotone" />}
                    title="Scratch Repair"
                    desc="Fills in missing pixels from physical damage (tears, dust, scratches)."
                    active={options.scratch_repair}
                    onClick={() => handleToggle('scratch_repair')}
                  />
                </div>
                
                <button 
                  onClick={handleRestore}
                  className="w-full relative group overflow-hidden bg-gold-600 hover:bg-gold-500 text-black font-bold py-4 rounded-xl transition-all duration-300 shadow-[0_0_20px_rgba(212,168,83,0.3)] hover:shadow-[0_0_30px_rgba(212,168,83,0.5)] flex items-center justify-center gap-2"
                >
                  <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full group-hover:animate-shimmer" />
                  <MagicWand weight="fill" className="text-xl" />
                  INITIALIZE RESTORATION
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}

      {loading && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="w-full max-w-xl mx-auto text-center py-20 flex flex-col items-center justify-center"
        >
          {/* Custom cinematic loader */}
          <div className="relative w-32 h-32 mb-12">
            <div className="absolute inset-0 border-t-2 border-gold-500 rounded-full animate-spin shadow-[0_0_15px_rgba(212,168,83,0.5)]" />
            <div className="absolute inset-2 border-b-2 border-dark-300 rounded-full animate-spin-slow" />
            <div className="absolute inset-4 border-l-2 border-gold-300 rounded-full animate-spin-reverse shadow-[0_0_10px_rgba(235,198,127,0.3)]" />
            <div className="absolute inset-0 flex items-center justify-center">
              <Sparkle weight="fill" className="text-3xl text-gold-500 animate-pulse" />
            </div>
          </div>
          
          <h2 className="font-serif text-2xl font-bold text-white mb-2 tracking-widest uppercase">Processing Sequence</h2>
          <p className="text-dark-300 mb-8 font-light text-sm tracking-widest uppercase">Executing Neural Operations</p>
          
          <ProgressBar progress={progress} />
        </motion.div>
      )}

      {error && !loading && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-2xl mx-auto glass-card p-8 bg-red-900/20 border border-red-500/30 text-center"
        >
          <div className="text-red-400 text-5xl mb-4 flex justify-center"><MagicWand weight="duotone" /></div>
          <h3 className="text-xl font-bold text-red-200 mb-2">Restoration Failed</h3>
          <p className="text-red-300/70 mb-6">{error}</p>
          <button 
            onClick={() => { setError(null); setFile(null); }}
            className="px-6 py-2 border border-red-500/50 text-red-400 rounded-full hover:bg-red-500/10 transition-colors text-sm font-bold tracking-widest uppercase"
          >
            Reset Workspace
          </button>
        </motion.div>
      )}

      {result && !loading && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="w-full flex flex-col items-center"
        >
          <div className="w-full mb-12 relative p-[1px] rounded-3xl overflow-hidden group">
            {/* Animated gradient border */}
            <div className="absolute inset-0 bg-gradient-to-r from-gold-500/20 via-gold-500/50 to-gold-500/20 opacity-50" />
            
            <div className="relative bg-black rounded-3xl p-2 md:p-6 shadow-2xl">
              <BeforeAfterSlider beforeSrc={URL.createObjectURL(file)} afterSrc={result} />
            </div>
          </div>
          
          <div className="flex gap-4">
            <a 
              href={result} 
              download={`restored_${file.name}`}
              className="px-8 py-3 bg-gold-600 hover:bg-gold-500 text-black rounded-full font-bold flex items-center gap-2 transition-all shadow-[0_0_15px_rgba(212,168,83,0.4)] hover:shadow-[0_0_25px_rgba(212,168,83,0.6)] uppercase tracking-widest text-sm"
            >
              <DownloadSimple weight="bold" /> Export Image
            </a>
            <button 
              onClick={() => { setResult(null); setFile(null); }}
              className="px-8 py-3 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-full font-bold transition-all uppercase tracking-widest text-sm"
            >
              New Restoration
            </button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

function ToggleOption({ icon, title, desc, active, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`text-left p-4 rounded-xl border transition-all duration-300 flex items-start gap-4 ${
        active 
          ? 'bg-gold-500/10 border-gold-500/40 shadow-[0_0_15px_rgba(212,168,83,0.1)]' 
          : 'bg-black/20 border-white/5 hover:border-white/20 hover:bg-white/5'
      }`}
    >
      <div className={`p-2 rounded-lg ${active ? 'bg-gold-500 text-black' : 'bg-white/5 text-dark-300'}`}>
        {React.cloneElement(icon, { className: "text-xl" })}
      </div>
      <div>
        <h4 className={`font-bold text-sm mb-1 ${active ? 'text-gold-400' : 'text-white'}`}>{title}</h4>
        <p className="text-xs text-dark-300 leading-relaxed font-light">{desc}</p>
      </div>
    </button>
  );
}
