import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { 
  Image, 
  Target, 
  Sparkle, 
  Stack, 
  Brain, 
  Books, 
  Lightning,
  ArrowRight,
  CodeBlock,
  Cpu,
  Atom,
  MagnifyingGlass,
  Wrench
} from '@phosphor-icons/react';

const FADE_UP_ANIMATION_VARIANTS = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 15 } },
};

export default function Home() {
  return (
    <div className="pt-32 pb-24 px-6 md:px-12 max-w-7xl mx-auto flex flex-col items-center">
      {/* Hero Section */}
      <motion.section 
        className="w-full flex flex-col items-center text-center relative z-10"
        initial="hidden"
        animate="show"
        viewport={{ once: true }}
        variants={{
          hidden: {},
          show: {
            transition: {
              staggerChildren: 0.15,
            },
          },
        }}
      >
        <motion.div variants={FADE_UP_ANIMATION_VARIANTS} className="mb-8 inline-flex items-center gap-2 px-4 py-1.5 bg-gold-500/10 border border-gold-500/20 rounded-full text-xs font-semibold text-gold-500 uppercase tracking-widest">
          <Sparkle weight="fill" className="text-gold-500" />
          AI-Powered Heritage Technology
        </motion.div>

        <motion.h1 
          variants={FADE_UP_ANIMATION_VARIANTS} 
          className="font-serif text-5xl md:text-7xl font-bold leading-tight mb-6 text-gradient"
        >
          Restore History.<br />Discover Heritage.
        </motion.h1>

        <motion.p 
          variants={FADE_UP_ANIMATION_VARIANTS} 
          className="text-lg md:text-xl text-dark-300 max-w-2xl mb-16"
        >
          Breathe new life into degraded historical photographs with AI restoration, 
          and unlock the stories behind the world's greatest monuments.
        </motion.p>

        <motion.div variants={FADE_UP_ANIMATION_VARIANTS} className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
          <Link to="/restore" className="glass-card p-8 group text-left relative overflow-hidden flex flex-col items-start">
            <div className="text-4xl text-gold-500 mb-5 bg-gold-500/10 p-4 rounded-2xl border border-gold-500/20">
              <Image weight="duotone" />
            </div>
            <h3 className="font-serif text-2xl font-bold mb-3 text-white">Restore a Photo</h3>
            <p className="text-sm text-dark-300 leading-relaxed mb-6">
              Upload a faded, scratched, or damaged historical photo. 
              Our 5-stage AI pipeline will denoise, repair, colorize, and upscale it.
            </p>
            <div className="mt-auto flex items-center gap-2 text-gold-500 font-medium group-hover:gap-3 transition-all duration-300">
              Try Restoration <ArrowRight weight="bold" />
            </div>
            
            {/* Hover subtle glow */}
            <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-gold-500/10 blur-3xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
          </Link>

          <Link to="/identify" className="glass-card p-8 group text-left relative overflow-hidden flex flex-col items-start">
            <div className="text-4xl text-gold-500 mb-5 bg-gold-500/10 p-4 rounded-2xl border border-gold-500/20">
              <Target weight="duotone" />
            </div>
            <h3 className="font-serif text-2xl font-bold mb-3 text-white">Identify a Monument</h3>
            <p className="text-sm text-dark-300 leading-relaxed mb-6">
              Snap a photo of any landmark. AI identifies it instantly and 
              delivers verified historical facts with source citations.
            </p>
            <div className="mt-auto flex items-center gap-2 text-gold-500 font-medium group-hover:gap-3 transition-all duration-300">
              Try Identification <ArrowRight weight="bold" />
            </div>
            
            {/* Hover subtle glow */}
            <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-gold-500/10 blur-3xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
          </Link>
        </motion.div>
      </motion.section>

      {/* Features Section */}
      <motion.section 
        className="w-full mt-32"
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-100px" }}
        variants={{
          hidden: {},
          show: {
            transition: { staggerChildren: 0.1 },
          },
        }}
      >
        <motion.h2 variants={FADE_UP_ANIMATION_VARIANTS} className="font-serif text-4xl text-center font-bold mb-16 text-white">
          How It Works
        </motion.h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { icon: <Stack weight="duotone" />, title: '5-Stage ML Pipeline', desc: 'Old photo repair → denoise → face restore → colorize → upscale. Each stage uses SOTA models.' },
            { icon: <Brain weight="duotone" />, title: 'Smart Recognition', desc: 'MobileNetV3 classifier identifies 50+ monuments from India and around the world with 90%+ accuracy.' },
            { icon: <Books weight="duotone" />, title: 'Grounded RAG', desc: 'Historical facts retrieved from verified sources (Wikipedia, UNESCO, ASI) — never AI-hallucinated.' },
            { icon: <Lightning weight="duotone" />, title: 'Fast & Accessible', desc: 'Standard restoration in under 15 seconds. Works on web and mobile. No account needed.' },
          ].map((feature, i) => (
            <motion.div key={i} variants={FADE_UP_ANIMATION_VARIANTS} className="glass-card p-6 flex flex-col items-center text-center">
              <div className="text-3xl text-gold-400 mb-4 bg-white/5 p-3 rounded-xl border border-white/10">
                {feature.icon}
              </div>
              <h3 className="text-lg font-bold mb-2 text-white">{feature.title}</h3>
              <p className="text-sm text-dark-300">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Tech Stack Section */}
      <motion.section 
        className="w-full mt-32"
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-100px" }}
        variants={{
          hidden: {},
          show: {
            transition: { staggerChildren: 0.1 },
          },
        }}
      >
        <motion.h2 variants={FADE_UP_ANIMATION_VARIANTS} className="font-serif text-4xl text-center font-bold mb-16 text-white">
          Built With
        </motion.h2>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            { icon: <CodeBlock weight="duotone" />, name: 'FastAPI', desc: 'Async Python' },
            { icon: <Wrench weight="duotone" />, name: 'PyTorch', desc: 'Deep learning' },
            { icon: <Atom weight="duotone" />, name: 'React', desc: 'Web frontend' },
            { icon: <MagnifyingGlass weight="duotone" />, name: 'FAISS', desc: 'Vector search' },
            { icon: <Cpu weight="duotone" />, name: 'LLama', desc: 'Grounded gen' },
            { icon: <Image weight="duotone" />, name: 'Real-ESRGAN', desc: '4x upscaling' },
          ].map((tech, i) => (
            <motion.div key={i} variants={FADE_UP_ANIMATION_VARIANTS} className="glass-card p-5 flex flex-col items-center text-center hover:-translate-y-1">
              <div className="text-2xl text-gold-500 mb-3">
                {tech.icon}
              </div>
              <h3 className="text-base font-semibold text-white mb-1">{tech.name}</h3>
              <p className="text-xs text-dark-400">{tech.desc}</p>
            </motion.div>
          ))}
        </div>
      </motion.section>
    </div>
  );
}
