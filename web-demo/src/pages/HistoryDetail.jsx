import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getHistory } from '../utils/api';
import { motion } from 'motion/react';
import { 
  ArrowLeft,
  MapPin,
  Clock,
  Hammer,
  Bank,
  Medal,
  Scroll,
  Timer,
  BookBookmark,
  LinkSimple
} from '@phosphor-icons/react';

export default function HistoryDetail() {
  const { id } = useParams();
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const data = await getHistory(id);
        setHistory(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [id]);

  if (loading) {
    return (
      <div className="pt-32 pb-20 px-6 min-h-screen flex justify-center items-center">
        <div className="w-10 h-10 rounded-full border-2 border-gold-500/30 border-t-gold-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="pt-32 pb-20 px-6 min-h-screen">
        <div className="p-8 text-center text-red-400 bg-red-500/10 border border-red-500/20 rounded-2xl max-w-2xl mx-auto">
          <p className="mb-4">Failed to load history: {error}</p>
          <Link to="/identify" className="btn-secondary inline-flex">
            <ArrowLeft weight="bold" /> Back to Identify
          </Link>
        </div>
      </div>
    );
  }

  if (!history) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }} 
      animate={{ opacity: 1, y: 0 }} 
      transition={{ duration: 0.5 }}
      className="pt-32 pb-20 px-6 max-w-4xl mx-auto min-h-screen"
    >
      {/* Header */}
      <div className="mb-12 relative">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gold-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 pointer-events-none" />

        <Link to="/identify" className="inline-flex items-center gap-2 text-sm text-dark-300 hover:text-gold-500 transition-colors mb-6">
          <ArrowLeft weight="bold" /> Back to Identify
        </Link>

        <h1 className="font-serif text-4xl md:text-6xl font-bold text-gradient leading-tight mb-6">
          {history.name}
        </h1>

        <div className="flex flex-wrap gap-4 text-sm text-dark-300">
          {history.location && (
            <span className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-lg border border-white/5">
              <MapPin weight="duotone" className="text-gold-500 text-lg" />
              {history.location}
            </span>
          )}
          {history.era && (
            <span className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-lg border border-white/5">
              <Clock weight="duotone" className="text-gold-500 text-lg" />
              {history.era}
            </span>
          )}
          {history.builder && (
            <span className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-lg border border-white/5">
              <Hammer weight="duotone" className="text-gold-500 text-lg" />
              {history.builder}
            </span>
          )}
          {history.architectural_style && (
            <span className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-lg border border-white/5">
              <Bank weight="duotone" className="text-gold-500 text-lg" />
              {history.architectural_style}
            </span>
          )}
          {history.unesco_status && (
            <span className="flex items-center gap-2 bg-gold-500/10 text-gold-400 px-4 py-2 rounded-lg border border-gold-500/20 font-medium">
              <Medal weight="duotone" className="text-lg" />
              {history.unesco_status}
            </span>
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="glass-card p-8 md:p-10 mb-8">
        <h2 className="font-serif text-2xl font-bold mb-6 text-gold-500 flex items-center gap-3">
          <Scroll weight="duotone" className="text-3xl" />
          Historical Summary
        </h2>
        <div className="text-base md:text-lg leading-relaxed text-dark-200 whitespace-pre-wrap">
          {history.summary}
        </div>
      </div>

      {/* Timeline */}
      {history.timeline?.length > 0 && (
        <div className="glass-card p-8 md:p-10 mb-8">
          <h2 className="font-serif text-2xl font-bold mb-8 text-gold-500 flex items-center gap-3">
            <Timer weight="duotone" className="text-3xl" />
            Timeline
          </h2>
          <div className="relative pl-8 border-l border-gold-500/30 space-y-8">
            {history.timeline.map((event, i) => (
              <div key={i} className="relative">
                <div className="absolute -left-[39px] top-1.5 w-4 h-4 bg-gold-500 rounded-full shadow-[0_0_10px_rgba(212,168,83,0.5)] border-4 border-[#111118]" />
                <div className="font-serif text-lg font-bold text-gold-400 mb-2">{event.year}</div>
                <div className="text-sm md:text-base text-dark-300 leading-relaxed">{event.event}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sources */}
      {history.sources?.length > 0 && (
        <div className="glass-card p-8 md:p-10">
          <h2 className="font-serif text-2xl font-bold mb-6 text-gold-500 flex items-center gap-3">
            <BookBookmark weight="duotone" className="text-3xl" />
            Sources
          </h2>
          <ul className="space-y-4">
            {history.sources.map((source, i) => (
              <li key={i} className="flex items-start gap-3 text-sm md:text-base border-b border-white/5 pb-4 last:border-0 last:pb-0">
                <LinkSimple weight="bold" className="text-gold-500 text-xl shrink-0 mt-0.5" />
                {source.url ? (
                  <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-white hover:text-gold-400 transition-colors">
                    {source.name}
                  </a>
                ) : (
                  <span className="text-dark-300">{source.name}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
}
