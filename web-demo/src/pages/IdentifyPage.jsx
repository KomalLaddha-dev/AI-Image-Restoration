import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import UploadZone from '../components/UploadZone';
import ProgressBar from '../components/ProgressBar';
import { identifyMonument } from '../api/client';
import { Target, WarningCircle, Sparkle } from '@phosphor-icons/react';

export default function IdentifyPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  const handleIdentify = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setProgress(0);
    
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 8, 90));
    }, 400);

    try {
      // Mock API call since actual endpoint might not be ready
      await new Promise(resolve => setTimeout(resolve, 2000));
      // const result = await identifyMonument(file);
      // const id = result.id;
      
      // Simulate successful identification
      const mockId = 'taj-mahal';
      setProgress(100);
      
      setTimeout(() => {
        navigate(`/history/${mockId}`);
      }, 500);
      
    } catch (err) {
      setError(err.message || 'Unable to identify monument. Please try another photo.');
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
          Monument <span className="italic text-gold-400 font-light">Analysis</span>
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-dark-300 max-w-xl mx-auto text-lg font-light"
        >
          Upload a photograph of any historical structure. Our neural network will identify it and retrieve verified historical data.
        </motion.p>
      </div>

      {!loading && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-3xl mx-auto flex flex-col items-center"
        >
          <UploadZone onFileSelect={setFile} file={file} />
          
          <AnimatePresence>
            {file && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="w-full mt-8 overflow-hidden"
              >
                <button 
                  onClick={handleIdentify}
                  className="w-full relative group overflow-hidden bg-gold-600 hover:bg-gold-500 text-black font-bold py-5 rounded-xl transition-all duration-300 shadow-[0_0_20px_rgba(212,168,83,0.3)] hover:shadow-[0_0_30px_rgba(212,168,83,0.5)] flex items-center justify-center gap-3 text-lg tracking-widest uppercase"
                >
                  <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full group-hover:animate-shimmer" />
                  <Target weight="fill" className="text-2xl" />
                  INITIATE SCAN
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {error && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-8 flex items-center gap-3 text-red-400 bg-red-900/20 px-6 py-4 rounded-xl border border-red-500/30 w-full"
            >
              <WarningCircle weight="fill" className="text-2xl shrink-0" />
              <p className="text-sm font-medium">{error}</p>
            </motion.div>
          )}
        </motion.div>
      )}

      {loading && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="w-full max-w-xl mx-auto text-center py-20 flex flex-col items-center justify-center"
        >
          <div className="relative w-32 h-32 mb-12">
            <div className="absolute inset-0 border-t-2 border-gold-500 rounded-full animate-spin shadow-[0_0_15px_rgba(212,168,83,0.5)]" />
            <div className="absolute inset-2 border-b-2 border-dark-300 rounded-full animate-spin-slow" />
            <div className="absolute inset-0 flex items-center justify-center">
              <Target weight="duotone" className="text-4xl text-gold-500 animate-pulse" />
            </div>
            
            {/* Scanning line effect */}
            <motion.div 
              animate={{ y: ["0%", "100%", "0%"] }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="absolute inset-x-4 top-4 h-[2px] bg-gold-400 shadow-[0_0_10px_rgba(212,168,83,1)] z-10"
            />
          </div>
          
          <h2 className="font-serif text-2xl font-bold text-white mb-2 tracking-widest uppercase">Cross-Referencing</h2>
          <p className="text-dark-300 mb-8 font-light text-sm tracking-widest uppercase">Scanning Architectural Database</p>
          
          <ProgressBar progress={progress} />
        </motion.div>
      )}
    </motion.div>
  );
}
