import React, { useCallback, useRef, useState } from 'react';
import { UploadSimple, FileImage } from '@phosphor-icons/react';

export default function UploadZone({ onFileSelect, accept = 'image/*', label = 'Upload a Photo' }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef(null);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    if (file && file.type.startsWith('image/')) {
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleClick = () => {
    inputRef.current?.click();
  };

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    if (file) onFileSelect(file);
  };

  return (
    <div
      className={`
        w-full p-12 flex flex-col items-center justify-center text-center
        rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer
        ${isDragOver 
          ? 'border-gold-500 bg-gold-500/10 shadow-[0_0_30px_rgba(212,168,83,0.15)]' 
          : 'border-white/10 bg-white/[0.02] hover:border-gold-500/50 hover:bg-white/[0.04]'
        }
      `}
      onClick={handleClick}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      role="button"
      tabIndex={0}
      aria-label={label}
    >
      <div className={`mb-6 p-4 rounded-full transition-colors duration-300 ${isDragOver ? 'bg-gold-500/20 text-gold-400' : 'bg-white/5 text-dark-300'}`}>
        <UploadSimple weight="duotone" className="text-4xl" />
      </div>
      <h3 className="text-xl font-bold mb-2 text-white">{label}</h3>
      <p className="text-dark-300 text-sm mb-4">Drag & drop an image here, or click to browse</p>
      
      <div className="flex items-center justify-center gap-2 text-xs font-medium text-dark-400 uppercase tracking-wider bg-white/5 px-3 py-1.5 rounded-md">
        <FileImage weight="duotone" />
        Supports JPEG, PNG, WebP — Max 20MB
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
      />
    </div>
  );
}
