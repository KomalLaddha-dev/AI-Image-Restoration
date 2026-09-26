import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, useScroll, useTransform } from 'framer-motion';
import { ArrowLeft, Clock, MapPin, Info, ArrowUpRight } from '@phosphor-icons/react';
import { getMonumentHistory } from '../api/client';

export default function HistoryDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  });

  const heroY = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  useEffect(() => {
    async function fetchHistory() {
      try {
        setLoading(true);
        const result = await getMonumentHistory(id);
        setData(result);
      } catch (err) {
        setError(err.message || 'Failed to load monument history.');
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [id]);

  if (loading) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center relative z-10">
        <div className="w-12 h-12 border-2 border-gold-500/20 border-t-gold-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center px-6 relative z-10">
        <div className="glass-card p-10 text-center max-w-lg">
          <Info weight="duotone" className="text-5xl text-gold-500 mx-auto mb-6" />
          <h2 className="font-serif text-2xl font-bold text-white mb-4">Record Not Found</h2>
          <p className="text-dark-300 mb-8 font-light leading-relaxed">
            {error || "The historical record for this monument could not be retrieved from the archives."}
          </p>
          <Link to="/identify" className="inline-flex items-center gap-2 text-gold-400 hover:text-gold-300 font-bold tracking-widest uppercase text-sm border-b border-gold-500/30 hover:border-gold-400 pb-1 transition-colors">
            <ArrowLeft weight="bold" /> Return to Scanner
          </Link>
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      ref={containerRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full relative z-10"
    >
      {/* Hero Header with Parallax */}
      <div className="relative w-full h-[70vh] flex flex-col justify-end overflow-hidden">
        {data.image_url && (
          <motion.div 
            style={{ y: heroY }}
            className="absolute inset-0 z-0"
          >
            <div className="absolute inset-0 bg-gradient-to-t from-bg-primary via-bg-primary/60 to-transparent z-10" />
            <img 
              src={data.image_url} 
              alt={data.name} 
              className="w-full h-full object-cover object-center opacity-40 mix-blend-luminosity"
            />
          </motion.div>
        )}
        
        <div className="relative z-20 w-full max-w-4xl mx-auto px-6 md:px-12 pb-16">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <Link to="/identify" className="inline-flex items-center gap-2 text-dark-300 hover:text-white text-xs font-bold tracking-widest uppercase mb-8 transition-colors">
              <ArrowLeft weight="bold" /> Back
            </Link>
            
            <h1 className="font-serif text-5xl md:text-8xl font-bold text-white mb-6 tracking-tight leading-[1.1]">{data.name}</h1>
            
            <div className="flex flex-wrap items-center gap-6 text-gold-400 font-medium tracking-wide uppercase text-sm">
              <span className="flex items-center gap-2"><MapPin weight="fill" /> {data.location}</span>
              <span className="flex items-center gap-2"><Clock weight="fill" /> {data.built_year}</span>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Editorial Content */}
      <div className="w-full max-w-4xl mx-auto px-6 md:px-12 py-20 pb-32">
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="prose prose-invert prose-lg max-w-none prose-headings:font-serif prose-headings:font-bold prose-p:font-light prose-p:text-dark-200 prose-p:leading-relaxed prose-a:text-gold-400"
        >
          {/* Drop cap for first paragraph */}
          <p className="first-letter:font-serif first-letter:float-left first-letter:text-7xl first-letter:pr-4 first-letter:text-gold-500 first-letter:font-bold first-line:uppercase first-line:tracking-widest">
            {data.description}
          </p>
        </motion.div>

        {data.timeline && data.timeline.length > 0 && (
          <div className="mt-32">
            <motion.h3 
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="font-serif text-3xl font-bold text-white mb-16 flex items-center gap-4"
            >
              <div className="h-[1px] flex-grow bg-white/10" />
              Historical Timeline
              <div className="h-[1px] flex-grow bg-white/10" />
            </motion.h3>

            <div className="relative border-l border-gold-500/20 ml-4 md:ml-8 space-y-16">
              {data.timeline.map((event, idx) => (
                <motion.div 
                  key={idx} 
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.6, delay: idx * 0.1 }}
                  className="relative pl-10 md:pl-16 group"
                >
                  <div className="absolute -left-[5px] top-1.5 w-[9px] h-[9px] rounded-full bg-gold-500 shadow-[0_0_10px_rgba(212,168,83,0.8)] group-hover:scale-150 transition-transform duration-300" />
                  
                  <div className="text-gold-400 font-bold tracking-widest text-sm mb-3 bg-white/5 inline-block px-3 py-1 rounded-md">
                    {event.year}
                  </div>
                  <h4 className="font-serif text-2xl font-bold text-white mb-3 group-hover:text-gold-200 transition-colors">
                    {event.title}
                  </h4>
                  <p className="text-dark-300 font-light leading-relaxed max-w-2xl">
                    {event.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {data.source_url && (
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mt-32 pt-12 border-t border-white/10"
          >
            <a 
              href={data.source_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center gap-3 text-gold-500 hover:text-gold-400 transition-colors font-bold tracking-widest uppercase text-sm group"
            >
              View Primary Source Material 
              <ArrowUpRight weight="bold" className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
            </a>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
