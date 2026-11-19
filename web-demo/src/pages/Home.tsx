import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Sparkle, 
  ArrowRight, 
  Stack, 
  Brain, 
  Books, 
  Lightning,
  Eye,
  Camera,
  SpeakerHigh
} from '@phosphor-icons/react';
import BeforeAfterSlider from '../components/BeforeAfterSlider';
import MonumentCard from '../components/MonumentCard';

export default function Home() {
  const curatedHeritage = [
    {
      id: 'taj_mahal',
      name: 'Taj Mahal',
      location: 'Agra, Uttar Pradesh, India',
      era: '1632–1653 CE',
      imageUrl: '/samples/taj_mahal.jpg',
      confidence: 0.98,
      category: 'monument',
    },
    {
      id: 'mahatma_gandhi',
      name: 'Mahatma Gandhi',
      location: 'Porbandar & New Delhi, India',
      era: '1869–1948 CE',
      imageUrl: '/samples/mahatma_gandhi.jpg',
      confidence: 0.97,
      category: 'historical_figure',
    },
    {
      id: 'swami_vivekananda',
      name: 'Swami Vivekananda',
      location: 'Kolkata & Belur Math, India',
      era: '1863–1902 CE',
      imageUrl: '/samples/swami_vivekananda.jpg',
      confidence: 0.95,
      category: 'historical_figure',
    },
    {
      id: 'qutub_minar',
      name: 'Qutub Minar',
      location: 'Delhi, India',
      era: '1192–1220 CE',
      imageUrl: '/samples/qutub_minar.jpg',
      confidence: 0.94,
      category: 'monument',
    },
    {
      id: 'br_ambedkar',
      name: 'Dr. B. R. Ambedkar',
      location: 'Mhow & New Delhi, India',
      era: '1891–1956 CE',
      imageUrl: '/samples/br_ambedkar.jpg',
      confidence: 0.96,
      category: 'historical_figure',
    },
    {
      id: 'colosseum',
      name: 'Colosseum',
      location: 'Rome, Italy',
      era: '70–80 CE',
      imageUrl: '/samples/colosseum.jpg',
      confidence: 0.91,
      category: 'monument',
    },
  ];

  return (
    <div className="w-full flex flex-col items-center">
      {/* ── 1. Hero Section: Editorial Gallery Wall ──────────────────────── */}
      <section className="w-full max-w-7xl mx-auto px-6 md:px-12 pt-16 md:pt-24 pb-16 flex flex-col items-center text-center">
        {/* Archival Provenance Eyebrow */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-accent-sepia-faint border border-accent-sepia/25 text-xs font-semibold uppercase tracking-widest text-accent-sepia mb-6"
        >
          <Sparkle weight="fill" className="text-sm" />
          AI Historical Reconstruction & Provenance
        </motion.div>

        {/* Serif Hero Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="font-heading text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-ink dark:text-ink-dark max-w-4xl leading-[1.1] mb-6"
        >
          Restore History. <br className="hidden sm:inline" />
          <span className="italic font-normal text-accent-sepia">Discover Heritage.</span>
        </motion.h1>

        {/* Subtext: Concise (< 20 words) */}
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="text-base sm:text-lg md:text-xl text-ink-muted dark:text-ink-muted-dark max-w-2xl font-normal leading-relaxed mb-10"
        >
          Neural reconstruction for faded historical photographs, paired with verified archival identification of global heritage.
        </motion.p>

        {/* Primary CTA Pairing */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto mb-16 md:mb-20"
        >
          <Link
            to="/restore"
            className="w-full sm:w-auto px-8 py-3.5 bg-accent-sepia hover:bg-accent-sepia-hover text-black font-semibold text-sm tracking-wider uppercase rounded-xl transition-all duration-200 shadow-md shadow-accent-sepia/25 hover:shadow-lg hover:shadow-accent-sepia/40 flex items-center justify-center gap-2"
          >
            <Sparkle weight="bold" /> Restore a Photo
          </Link>

          <Link
            to="/identify"
            className="w-full sm:w-auto px-8 py-3.5 bg-surface dark:bg-surface-dark hover:bg-surface-subtle dark:hover:bg-surface-dark/80 text-ink dark:text-ink-dark border border-border-theme hover:border-accent-sepia/50 font-semibold text-sm tracking-wider uppercase rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
          >
            <Camera weight="bold" /> Identify a Monument
          </Link>
        </motion.div>

        {/* ── 2. Visual Centerpiece: Before/After Slider ──────────────────── */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-5xl mx-auto mb-6"
        >
          <div className="relative p-2 md:p-3 rounded-3xl bg-surface/70 dark:bg-surface-dark/70 border border-border-theme shadow-2xl backdrop-blur-sm">
            <BeforeAfterSlider
              beforeSrc="/samples/taj_mahal_hero_degraded.jpg"
              afterSrc="/samples/taj_mahal_restored.jpg"
              beforeLabel="Original / Degraded"
              afterLabel="AI Restored"
              aspectRatio="aspect-[4/3] md:aspect-[16/10]"
              autoAnimate={true}
            />
          </div>

          <div className="flex items-center justify-between px-4 mt-3 text-xs text-ink-muted dark:text-ink-muted-dark">
            <span className="flex items-center gap-1.5">
              <Eye weight="duotone" className="text-accent-sepia" />
              Drag the divider or touch to compare details
            </span>
            <span className="hidden sm:inline font-mono">BOPBTL + DDColor + GFPGAN</span>
          </div>
        </motion.div>
      </section>

      {/* ── 3. Engineering & Historical Foundation Grid ─────────────────── */}
      <section className="w-full border-t border-border-theme bg-surface-subtle/50 dark:bg-surface-dark/30 py-20 px-6 md:px-12 transition-colors duration-300">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="font-heading text-3xl md:text-4xl font-bold text-ink dark:text-ink-dark mb-4">
              Restoration Science & Provenance
            </h2>
            <p className="text-sm md:text-base text-ink-muted dark:text-ink-muted-dark leading-relaxed">
              Every photograph is reconstructed through five precision tensor stages; every identification is anchored in verified records.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: <Stack weight="duotone" />,
                title: '5-Stage Pipeline',
                desc: 'Scratches, grain, blur, color loss, and facial details are treated sequentially with specialized models.',
              },
              {
                icon: <Brain weight="duotone" />,
                title: 'Landmark & Figure AI',
                desc: 'Visual recognition identifies architectural monuments and prominent historical personalities with calibrated certainty.',
              },
              {
                icon: <SpeakerHigh weight="duotone" />,
                title: 'Audio Voice Narration',
                desc: 'Built-in text-to-speech audio narration reads verified historical provenance and significance aloud.',
              },
              {
                icon: <Books weight="duotone" />,
                title: 'Grounded Records',
                desc: 'Zero hallucinated timelines. Every summary and milestone is sourced directly from academic corpus archives.',
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="p-8 rounded-2xl border border-border-theme bg-surface dark:bg-surface-dark flex flex-col items-start transition-all duration-200 hover:border-accent-sepia/40 shadow-sm"
              >
                <div className="w-12 h-12 rounded-xl bg-accent-sepia-faint border border-accent-sepia/20 flex items-center justify-center text-accent-sepia text-2xl mb-6">
                  {feature.icon}
                </div>
                <h3 className="font-heading text-xl font-bold text-ink dark:text-ink-dark mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-ink-muted dark:text-ink-muted-dark leading-relaxed">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 4. Curated Heritage Browse (Monuments & Historical Figures) ───── */}
      <section className="w-full max-w-7xl mx-auto py-24 px-6 md:px-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-4">
          <div>
            <h2 className="font-heading text-3xl md:text-4xl font-bold text-ink dark:text-ink-dark mb-2">
              Archival Heritage & Historical Figures
            </h2>
            <p className="text-sm md:text-base text-ink-muted dark:text-ink-muted-dark">
              Explore global monuments and iconic historical leaders with verified provenance, restoration studies, and audio narration.
            </p>
          </div>

          <Link
            to="/identify"
            className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-accent-sepia hover:text-accent-sepia-hover transition-colors"
          >
            Identify Your Photo <ArrowRight weight="bold" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8">
          {curatedHeritage.map((m) => (
            <MonumentCard
              key={m.id}
              id={m.id}
              name={m.name}
              location={m.location}
              era={m.era}
              imageUrl={m.imageUrl}
              confidence={m.confidence}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
