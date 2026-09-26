import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadSimple, FileImage, Image as ImageIcon } from '@phosphor-icons/react';
import { motion, AnimatePresence } from 'framer-motion';

export default function UploadZone({ onFileSelect, file, accept = "image/jpeg, image/png, image/webp" }) {
  const [isHovered, setIsHovered] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles?.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept.split(', ').reduce((acc, curr) => ({ ...acc, [curr]: [] }), {}),
    maxFiles: 1,
    multiple: false
  });

  return (
    <motion.div
      {...getRootProps()}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      animate={{
        scale: isDragActive ? 0.98 : 1,
        borderColor: isDragActive ? "rgba(212,168,83,0.8)" : isHovered ? "rgba(212,168,83,0.4)" : "rgba(255,255,255,0.1)",
        backgroundColor: isDragActive ? "rgba(212,168,83,0.05)" : "rgba(0,0,0,0.4)"
      }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="relative w-full p-12 rounded-3xl border-2 border-dashed cursor-pointer overflow-hidden flex flex-col items-center justify-center text-center outline-none backdrop-blur-xl group shadow-2xl"
    >
      <input {...getInputProps()} />
      
      {/* Background glow effect on drag */}
      <AnimatePresence>
        {isDragActive && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-gold-500/10 mix-blend-screen pointer-events-none" 
          />
        )}
      </AnimatePresence>

      <motion.div 
        animate={{ y: isDragActive ? -10 : 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
        className="relative z-10 flex flex-col items-center"
      >
        <div className="relative mb-6">
          <div className="absolute inset-0 bg-gold-500/20 rounded-full blur-xl scale-150 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="bg-white/5 border border-white/10 p-5 rounded-full shadow-[0_0_30px_rgba(0,0,0,0.5)] relative">
            <UploadSimple weight="duotone" className="text-4xl text-gold-400 group-hover:text-gold-300 transition-colors duration-300" />
          </div>
        </div>

        <h3 className="font-serif text-2xl font-bold text-white mb-3">
          {isDragActive ? "Drop to Upload" : "Upload an Image"}
        </h3>
        
        <p className="text-dark-300 text-sm mb-6 max-w-xs font-light">
          Drag & drop a historical photograph here, or click to browse your files.
        </p>

        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-dark-400 bg-white/5 px-4 py-2 rounded-full border border-white/5">
          <FileImage weight="bold" />
          Supports JPEG, PNG, WEBP — Max 20MB
        </div>
      </motion.div>
      
      {file && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute inset-0 bg-black/80 backdrop-blur-md flex flex-col items-center justify-center z-20 border border-gold-500/30 rounded-3xl"
        >
          <ImageIcon weight="duotone" className="text-5xl text-gold-500 mb-4" />
          <p className="text-lg font-bold text-white mb-1 truncate max-w-[80%]">{file.name}</p>
          <p className="text-sm text-gold-400 uppercase tracking-widest font-semibold">Ready to process</p>
          <button 
            className="mt-6 text-xs text-dark-300 hover:text-white uppercase tracking-widest transition-colors duration-300 border-b border-dark-300 hover:border-white pb-1"
            onClick={(e) => { e.stopPropagation(); onFileSelect(null); }}
          >
            Choose a different file
          </button>
        </motion.div>
      )}
    </motion.div>
  );
}
