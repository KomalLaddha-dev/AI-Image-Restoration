import React, { useCallback, useMemo } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadSimple, FileImage, ArrowsClockwise, Sparkle } from '@phosphor-icons/react';

interface UploadZoneProps {
  file: File | null;
  onFileSelect: (file: File | null) => void;
  accept?: string;
  title?: string;
  subtext?: string;
  actionLabel?: string;
  onAction?: () => void;
  disabled?: boolean;
}

export default function UploadZone({
  file,
  onFileSelect,
  accept = 'image/jpeg, image/png, image/webp',
  title = 'Upload Archival Photograph',
  subtext = 'Drag & drop a historical photo, or click to browse files',
  actionLabel,
  onAction,
  disabled = false,
}: UploadZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles?.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const acceptConfig = useMemo(() => {
    return accept.split(', ').reduce<Record<string, string[]>>((acc, curr) => {
      acc[curr.trim()] = [];
      return acc;
    }, {});
  }, [accept]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptConfig,
    maxFiles: 1,
    multiple: false,
    disabled: disabled || Boolean(file),
  });

  const previewUrl = useMemo(() => {
    if (!file) return null;
    return URL.createObjectURL(file);
  }, [file]);

  return (
    <div className="w-full relative">
      {!file ? (
        <div
          {...getRootProps()}
          className={`relative w-full p-10 md:p-14 rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer overflow-hidden flex flex-col items-center justify-center text-center outline-none ${
            isDragActive
              ? 'border-accent-sepia bg-accent-sepia-faint scale-[0.99]'
              : 'border-border-theme hover:border-accent-sepia/60 bg-surface/50 dark:bg-surface-dark/40 hover:bg-surface-subtle dark:hover:bg-surface-dark/70'
          }`}
        >
          <input {...getInputProps()} />

          {/* Narrow Glassmorphism Drag Highlight */}
          {isDragActive && (
            <div className="absolute inset-0 glass-panel border border-accent-sepia/40 pointer-events-none flex items-center justify-center z-20">
              <span className="text-sm font-semibold tracking-wider uppercase text-accent-sepia flex items-center gap-2">
                <Sparkle weight="fill" /> Release to Load Photo
              </span>
            </div>
          )}

          {/* Central Upload Prompt */}
          <div className="relative z-10 flex flex-col items-center">
            <div className="w-14 h-14 rounded-full bg-accent-sepia-faint border border-accent-sepia/25 flex items-center justify-center text-accent-sepia mb-5 transition-transform duration-300 group-hover:scale-105">
              <UploadSimple weight="duotone" className="text-2xl" />
            </div>

            <h3 className="font-heading text-2xl md:text-3xl font-semibold text-ink dark:text-ink-dark mb-2">
              {title}
            </h3>

            <p className="text-sm text-ink-muted dark:text-ink-muted-dark max-w-sm mb-6 leading-relaxed">
              {subtext}
            </p>

            <div className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-ink-faint dark:text-ink-faint-dark bg-black/5 dark:bg-white/5 px-3.5 py-1.5 rounded-full border border-border-theme">
              <FileImage weight="bold" />
              JPEG, PNG, WebP • Up to 20MB
            </div>
          </div>
        </div>
      ) : (
        /* Image Preview with Floating Glass CTA */
        <div className="relative w-full rounded-2xl overflow-hidden border border-border-theme shadow-2xl bg-black">
          <div className="relative aspect-[4/3] md:aspect-[16/10] w-full">
            <img
              src={previewUrl!}
              alt="Uploaded Preview"
              className="w-full h-full object-contain bg-black/90"
            />
            {/* Subtle Gradient Scrim at Bottom */}
            <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-black/85 via-black/40 to-transparent pointer-events-none" />

            {/* Floating Glassmorphism Action Bar */}
            <div className="absolute inset-x-4 bottom-4 md:inset-x-8 md:bottom-6 flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl glass-panel z-20">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 rounded-lg bg-accent-sepia-faint border border-accent-sepia/30 flex items-center justify-center text-accent-sepia-light shrink-0">
                  <FileImage weight="duotone" className="text-xl" />
                </div>
                <div className="truncate text-left">
                  <p className="text-xs text-white/60 uppercase tracking-wider font-semibold">Loaded Photograph</p>
                  <p className="text-sm font-medium text-white truncate max-w-[220px] md:max-w-xs">{file.name}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <button
                  type="button"
                  onClick={() => onFileSelect(null)}
                  className="px-4 py-2 text-xs font-semibold uppercase tracking-wider text-white/80 hover:text-white border border-white/20 hover:border-white/40 rounded-lg transition-colors flex items-center justify-center gap-1.5"
                >
                  <ArrowsClockwise weight="bold" /> Change
                </button>

                {onAction && actionLabel && (
                  <button
                    type="button"
                    onClick={onAction}
                    className="flex-1 sm:flex-initial px-6 py-2.5 bg-accent-sepia hover:bg-accent-sepia-hover text-black font-semibold text-xs tracking-wider uppercase rounded-lg shadow-lg shadow-accent-sepia/20 transition-all hover:shadow-accent-sepia/40 flex items-center justify-center gap-2"
                  >
                    <Sparkle weight="fill" /> {actionLabel}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
