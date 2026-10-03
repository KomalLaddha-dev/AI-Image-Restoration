import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MagicWand, 
  DownloadSimple, 
  ArrowsClockwise, 
  Faders, 
  DropHalfBottom, 
  CameraRotate, 
  Sliders,
  WarningCircle,
  CheckCircle,
  CircleNotch,
  Clock,
  MinusCircle,
  Sparkle
} from '@phosphor-icons/react';
import UploadZone from '../components/UploadZone';
import BeforeAfterSlider from '../components/BeforeAfterSlider';
import ProgressBar from '../components/ProgressBar';
import { restoreSync } from '../utils/api';
import type { RestoreOptions, RestoreResult } from '../types';

/** A single stage in the restoration pipeline display. */
interface PipelineStage {
  id: string;
  label: string;
  tag: string;
  status: 'waiting' | 'processing' | 'completed' | 'skipped' | 'failed';
  skipReason?: string;
}

/**
 * Build the ordered pipeline stages based on user-selected options.
 * Old Photo Repair (BOPBTL) is always first and always runs.
 * Upscale (Real-ESRGAN) is always last and always runs.
 * The three optional stages in-between depend on the user's toggle state.
 */
function buildPipelineStages(options: RestoreOptions): PipelineStage[] {
  const stages: PipelineStage[] = [];

  // Always-on: Old Photo Repair
  stages.push({
    id: 'old_photo_repair',
    label: 'Old Photo Defect Repair',
    tag: 'BOPBTL',
    status: 'waiting',
  });

  // Optional: Denoise/Deblur
  stages.push({
    id: 'denoise',
    label: 'Denoise & Deblur',
    tag: 'NAFNet',
    status: options.denoise ? 'waiting' : 'skipped',
    skipReason: options.denoise ? undefined : 'Disabled by user',
  });

  // Optional: Face Restore
  stages.push({
    id: 'face_restore',
    label: 'Facial Detail Reconstruction',
    tag: 'GFPGAN',
    status: options.face_restore ? 'waiting' : 'skipped',
    skipReason: options.face_restore ? undefined : 'Disabled by user',
  });

  // Optional: Colorize
  stages.push({
    id: 'colorize',
    label: 'Historical Colorization',
    tag: 'DDColor',
    status: options.colorize ? 'waiting' : 'skipped',
    skipReason: options.colorize ? undefined : 'Disabled by user',
  });

  // Optional: Generative Enhancement
  stages.push({
    id: 'generative',
    label: 'Generative Enhancement',
    tag: 'HYPIR',
    status: options.generative ? 'waiting' : 'skipped',
    skipReason: options.generative ? undefined : 'Disabled by user',
  });

  // Always-on: Upscale
  stages.push({
    id: 'upscale',
    label: 'Final Composite & Upscale',
    tag: 'Real-ESRGAN',
    status: 'waiting',
  });

  return stages;
}

export default function RestorePage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RestoreResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<RestoreOptions>({
    denoise: true,
    colorize: true,
    face_restore: true,
    generative: false,
  });

  // Pipeline stages state — built dynamically from options
  const [pipelineStages, setPipelineStages] = useState<PipelineStage[]>([]);

  const handleToggle = (key: keyof RestoreOptions) => {
    setOptions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Compute overall progress from pipeline stages
  const overallProgress = useMemo(() => {
    if (pipelineStages.length === 0) return 0;
    const total = pipelineStages.length;
    const done = pipelineStages.filter(
      (s) => s.status === 'completed' || s.status === 'skipped'
    ).length;
    const processing = pipelineStages.filter((s) => s.status === 'processing').length;
    return Math.round(((done + processing * 0.5) / total) * 100);
  }, [pipelineStages]);

  const currentStageName = useMemo(() => {
    const processing = pipelineStages.find((s) => s.status === 'processing');
    if (processing) return `${processing.label} (${processing.tag})`;
    const waiting = pipelineStages.find((s) => s.status === 'waiting');
    if (waiting) return 'Preparing pipeline...';
    return 'Finalizing...';
  }, [pipelineStages]);

  // Count how many enabled (non-skipped) stages there are for the button label
  const enabledStageCount = useMemo(() => {
    const stages = buildPipelineStages(options);
    return stages.filter((s) => s.status !== 'skipped').length;
  }, [options]);

  const handleRestore = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    // Build stages from current options
    const stages = buildPipelineStages(options);
    setPipelineStages(stages);

    // Simulate stage progression for each enabled stage
    const enabledStages = stages.filter((s) => s.status !== 'skipped');
    let stageIdx = 0;

    const advanceStage = () => {
      setPipelineStages((prev) => {
        const updated = [...prev];
        // Complete the current processing stage
        const processingIdx = updated.findIndex((s) => s.status === 'processing');
        if (processingIdx >= 0) {
          updated[processingIdx] = { ...updated[processingIdx], status: 'completed' };
        }
        // Find the next waiting (non-skipped) stage and set it to processing
        const nextWaiting = updated.findIndex((s) => s.status === 'waiting');
        if (nextWaiting >= 0) {
          updated[nextWaiting] = { ...updated[nextWaiting], status: 'processing' };
        }
        return updated;
      });
    };

    // Start the first enabled stage
    advanceStage();

    const interval = setInterval(() => {
      stageIdx++;
      if (stageIdx < enabledStages.length) {
        advanceStage();
      }
    }, 1200);

    try {
      const payloadOptions = {
        ...options,
        mode: options.generative ? 'enhanced' : 'standard',
        generative_provider: options.generative ? 'colab' : 'off'
      };
      
      const res = await restoreSync(file, payloadOptions);
      clearInterval(interval);
      // Mark all remaining stages as completed
      setPipelineStages((prev) =>
        prev.map((s) =>
          s.status === 'processing' || s.status === 'waiting'
            ? { ...s, status: 'completed' }
            : s
        )
      );
      setResult(res);
    } catch (err: any) {
      clearInterval(interval);
      // Mark current processing stage as failed
      setPipelineStages((prev) =>
        prev.map((s) =>
          s.status === 'processing' ? { ...s, status: 'failed' } : s
        )
      );
      setError(err.message || 'Restoration failed. Please check the backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const originalUrl = file ? URL.createObjectURL(file) : null;

  return (
    <div className="w-full max-w-7xl mx-auto px-6 md:px-12 py-12 md:py-20 flex flex-col items-center">
      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <div className="text-center max-w-2xl mx-auto mb-12">
        <h1 className="font-heading text-4xl sm:text-5xl font-bold tracking-tight text-ink dark:text-ink-dark mb-3">
          Historical Photo <span className="italic font-normal text-accent-sepia">Restoration</span>
        </h1>
        <p className="text-sm md:text-base text-ink-muted dark:text-ink-muted-dark leading-relaxed">
          Reconstruct damaged emulsion, remove silver grain noise, recover lost facial detail, and restore authentic period color.
        </p>
      </div>

      {/* ── 1. Upload & Pipeline Config State ───────────────────────────── */}
      {!result && !loading && (
        <div className="w-full max-w-3xl flex flex-col items-center gap-8">
          <UploadZone
            file={file}
            onFileSelect={setFile}
            actionLabel="Initialize Restoration"
            onAction={handleRestore}
          />

          {file && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="w-full rounded-2xl border border-border-theme bg-surface dark:bg-surface-dark p-6 md:p-8 shadow-sm"
            >
              <div className="flex items-center gap-2.5 mb-6 pb-4 border-b border-border-theme">
                <Faders weight="duotone" className="text-xl text-accent-sepia" />
                <h3 className="font-heading text-lg font-bold text-ink dark:text-ink-dark">
                  Neural Pipeline Configuration
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <PipelineToggle
                  active={options.denoise}
                  onClick={() => handleToggle('denoise')}
                  icon={<Sliders weight="duotone" />}
                  title="Denoise / Deblur"
                  tag="NAFNet"
                  desc="Removes camera shake, silver grain, and optical scratches."
                />
                <PipelineToggle
                  active={options.face_restore}
                  onClick={() => handleToggle('face_restore')}
                  icon={<CameraRotate weight="duotone" />}
                  title="Facial Detail"
                  tag="GFPGAN"
                  desc="Reconstructs eyes, hair, and skin texture using GAN priors."
                />
                <PipelineToggle
                  active={options.colorize}
                  onClick={() => handleToggle('colorize')}
                  icon={<DropHalfBottom weight="duotone" />}
                  title="Period Color"
                  tag="DDColor"
                  desc="Injects historically calibrated pigments based on scene semantics."
                />
                <PipelineToggle
                  active={options.generative}
                  onClick={() => handleToggle('generative')}
                  icon={<Sparkle weight="duotone" />}
                  title="Generative Enhance"
                  tag="HYPIR"
                  desc="Reconstructs complex architectural textures using latent diffusion."
                />
              </div>

              <button
                type="button"
                onClick={handleRestore}
                className="w-full py-4 bg-accent-sepia hover:bg-accent-sepia-hover text-black font-semibold text-sm tracking-wider uppercase rounded-xl transition-all duration-200 shadow-md shadow-accent-sepia/25 hover:shadow-lg hover:shadow-accent-sepia/40 flex items-center justify-center gap-2"
              >
                <MagicWand weight="bold" className="text-lg" />
                Run {enabledStageCount}-Stage Restoration Pipeline
              </button>
            </motion.div>
          )}

          {error && (
            <div className="w-full p-5 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300 flex items-start gap-3">
              <WarningCircle weight="fill" className="text-xl shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold">Restoration Interrupted</h4>
                <p className="text-xs mt-1 leading-relaxed opacity-90">{error}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── 2. Loading / Processing Sequence — Dynamic Pipeline Stages ── */}
      {loading && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-xl mx-auto py-16 flex flex-col items-center text-center"
        >
          <div className="w-16 h-16 rounded-full border-2 border-accent-sepia-faint border-t-accent-sepia animate-spin mb-8" />
          <h2 className="font-heading text-2xl font-bold text-ink dark:text-ink-dark mb-2">
            Reconstructing Photograph
          </h2>
          <p className="text-xs font-mono uppercase tracking-widest text-accent-sepia mb-8">
            {currentStageName}
          </p>

          <ProgressBar progress={overallProgress} stageName={currentStageName} />

          {/* Dynamic Pipeline Stage List */}
          <div className="w-full mt-10 space-y-3">
            {pipelineStages.map((stage) => (
              <PipelineStageRow key={stage.id} stage={stage} />
            ))}
          </div>
        </motion.div>
      )}

      {/* ── 3. Restored Result: Signature Before/After Slider ───────────── */}
      {result && originalUrl && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="w-full flex flex-col items-center"
        >
          {/* Slider Container */}
          <div className="w-full max-w-5xl rounded-3xl p-2 md:p-3 bg-surface dark:bg-surface-dark border border-border-theme shadow-2xl mb-8">
            <BeforeAfterSlider
              beforeSrc={originalUrl}
              afterSrc={result.url}
              beforeLabel="Original Archival"
              afterLabel="Neural Restored"
              aspectRatio="aspect-[4/3] md:aspect-[16/10]"
            />
          </div>

          {/* Action Row */}
          <div className="flex flex-wrap items-center justify-center gap-4">
            <a
              href={result.url}
              download={`restored_${file?.name || 'heritage'}.png`}
              className="px-8 py-3.5 bg-accent-sepia hover:bg-accent-sepia-hover text-black font-semibold text-xs tracking-wider uppercase rounded-xl shadow-md shadow-accent-sepia/25 hover:shadow-lg hover:shadow-accent-sepia/40 transition-all flex items-center gap-2"
            >
              <DownloadSimple weight="bold" className="text-base" /> Download Restored File
            </a>

            <button
              type="button"
              onClick={() => {
                setResult(null);
                setFile(null);
                setError(null);
              }}
              className="px-6 py-3.5 bg-surface dark:bg-surface-dark hover:bg-surface-subtle dark:hover:bg-surface-dark/80 text-ink dark:text-ink-dark border border-border-theme hover:border-accent-sepia/50 font-semibold text-xs tracking-wider uppercase rounded-xl transition-colors flex items-center gap-2"
            >
              <ArrowsClockwise weight="bold" /> Restore Another Photo
            </button>
          </div>

          {/* Stage Summary */}
          {pipelineStages.length > 0 && (
            <div className="w-full max-w-xl mt-10 space-y-2">
              <h4 className="text-xs font-mono uppercase tracking-widest text-accent-sepia mb-3">
                Pipeline Summary
              </h4>
              {pipelineStages.map((stage) => (
                <PipelineStageRow key={stage.id} stage={stage} />
              ))}
            </div>
          )}

          {result.processingTime > 0 && (
            <p className="text-xs text-ink-muted dark:text-ink-muted-dark mt-6 font-mono">
              Inference time: {(result.processingTime / 1000).toFixed(2)}s • Stages: {result.stages.join(', ')}
            </p>
          )}
        </motion.div>
      )}
    </div>
  );
}

/** Renders a single pipeline stage row with its current status */
function PipelineStageRow({ stage }: { stage: PipelineStage }) {
  const statusConfig = {
    waiting: {
      icon: <Clock weight="duotone" className="text-ink-muted" />,
      label: 'Waiting',
      className: 'text-ink-muted dark:text-ink-muted-dark',
      bgClass: 'bg-surface-subtle/50 dark:bg-surface-dark/40',
    },
    processing: {
      icon: <CircleNotch weight="bold" className="text-accent-sepia animate-spin" />,
      label: 'Processing',
      className: 'text-accent-sepia',
      bgClass: 'bg-accent-sepia-faint border-accent-sepia/30',
    },
    completed: {
      icon: <CheckCircle weight="fill" className="text-accent-green" />,
      label: 'Completed',
      className: 'text-accent-green',
      bgClass: 'bg-accent-green-faint/50',
    },
    skipped: {
      icon: <MinusCircle weight="duotone" className="text-ink-faint" />,
      label: stage.skipReason ? `Skipped — ${stage.skipReason.toLowerCase()}` : 'Skipped',
      className: 'text-ink-faint',
      bgClass: 'bg-surface-subtle/30 dark:bg-surface-dark/20 opacity-60',
    },
    failed: {
      icon: <WarningCircle weight="fill" className="text-red-500" />,
      label: 'Failed',
      className: 'text-red-500',
      bgClass: 'bg-red-500/5 border-red-500/20',
    },
  };

  const config = statusConfig[stage.status];

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-xl border border-border-theme transition-all duration-200 ${config.bgClass}`}
    >
      <div className="shrink-0 text-lg">{config.icon}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-ink dark:text-ink-dark truncate">
            {stage.label}
          </span>
          <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-black/5 dark:bg-white/5 text-ink-muted shrink-0">
            {stage.tag}
          </span>
        </div>
      </div>
      <span className={`text-[11px] font-semibold uppercase tracking-wider shrink-0 ${config.className}`}>
        {config.label}
      </span>
    </div>
  );
}

function PipelineToggle({
  active,
  onClick,
  icon,
  title,
  tag,
  desc,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  title: string;
  tag: string;
  desc: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`p-5 rounded-xl border text-left transition-all duration-200 flex flex-col justify-between ${
        active
          ? 'bg-accent-sepia-faint border-accent-sepia/40 shadow-sm'
          : 'bg-surface-subtle/50 dark:bg-surface-dark/40 border-border-theme hover:border-border-theme/80 opacity-70 hover:opacity-100'
      }`}
    >
      <div className="flex items-center justify-between w-full mb-3">
        <div
          className={`w-9 h-9 rounded-lg flex items-center justify-center text-lg ${
            active ? 'bg-accent-sepia text-black' : 'bg-black/5 dark:bg-white/5 text-ink-muted'
          }`}
        >
          {icon}
        </div>
        <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-black/5 dark:bg-white/5 text-ink-muted">
          {tag}
        </span>
      </div>

      <div>
        <h4 className={`text-sm font-semibold mb-1 ${active ? 'text-accent-sepia' : 'text-ink dark:text-ink-dark'}`}>
          {title}
        </h4>
        <p className="text-xs text-ink-muted dark:text-ink-muted-dark leading-relaxed font-normal">
          {desc}
        </p>
      </div>
    </button>
  );
}
