import React, { useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Canvas } from '@react-three/fiber';
import DustParticles from '../components/DustParticles';
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

export default function Home() {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  });

  const heroY = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  
  return (
    <motion.div 
      ref={containerRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.5 } }}
      className="w-full"
    >
      {/* 3D Background */}
      <div className="fixed inset-0 z-0 pointer-events-none mix-blend-screen opacity-60">
        <Canvas camera={{ position: [0, 0, 10], fov: 75 }}>
          <ambientLight intensity={0.5} />
          <DustParticles count={1000} />
        </Canvas>
      </div>

      {/* Hero Section */}
      <motion.section 
        style={{ y: heroY, opacity: heroOpacity }}
        className="relative z-10 w-full min-h-screen flex flex-col items-center justify-center text-center px-6 md:px-12"
      >
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="mb-8 inline-flex items-center gap-2 px-4 py-1.5 bg-gold-500/10 border border-gold-500/20 rounded-full text-xs font-semibold text-gold-500 uppercase tracking-widest backdrop-blur-md"
        >
          <Sparkle weight="fill" className="text-gold-500" />
          AI-Powered Heritage Technology
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="font-serif text-5xl md:text-8xl font-bold leading-[1.1] mb-8 text-white tracking-tight"
        >
          Restore <span className="text-gradient italic font-light pr-2">History.</span><br />
          Discover <span className="text-gradient italic font-light pr-2">Heritage.</span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="text-lg md:text-xl text-dark-200 max-w-2xl font-light leading-relaxed"
        >
          Breathe new life into degraded historical photographs with AI restoration, 
          and unlock the stories behind the world's greatest monuments.
        </motion.p>
      </motion.section>

      {/* Interactive Cards Section */}
      <section className="relative z-20 w-full bg-bg-primary/50 backdrop-blur-3xl border-t border-white/5 py-32 px-6 md:px-12">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
          
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <Link to="/restore" className="block h-full glass-card p-10 group text-left relative overflow-hidden flex flex-col items-start bg-black/40 hover:bg-black/60 transition-colors duration-500 border border-white/10 hover:border-gold-500/30">
              <div className="absolute inset-0 bg-gradient-to-br from-gold-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              <div className="text-5xl text-gold-500 mb-8 bg-black p-5 rounded-2xl border border-white/10 shadow-2xl relative z-10">
                <Image weight="duotone" />
              </div>
              
              <h3 className="font-serif text-3xl font-bold mb-4 text-white relative z-10">Restore a Photo</h3>
              
              <p className="text-base text-dark-300 leading-relaxed mb-10 relative z-10 max-w-md">
                Upload a faded, scratched, or damaged historical photo. 
                Our 5-stage AI pipeline will denoise, repair, colorize, and upscale it to stunning clarity.
              </p>
              
              <div className="mt-auto flex items-center gap-2 text-gold-500 font-medium group-hover:gap-4 transition-all duration-300 relative z-10">
                Begin Restoration <ArrowRight weight="bold" />
              </div>
            </Link>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          >
            <Link to="/identify" className="block h-full glass-card p-10 group text-left relative overflow-hidden flex flex-col items-start bg-black/40 hover:bg-black/60 transition-colors duration-500 border border-white/10 hover:border-gold-500/30">
              <div className="absolute inset-0 bg-gradient-to-br from-gold-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              <div className="text-5xl text-gold-500 mb-8 bg-black p-5 rounded-2xl border border-white/10 shadow-2xl relative z-10">
                <Target weight="duotone" />
              </div>
              
              <h3 className="font-serif text-3xl font-bold mb-4 text-white relative z-10">Identify a Monument</h3>
              
              <p className="text-base text-dark-300 leading-relaxed mb-10 relative z-10 max-w-md">
                Snap a photo of any landmark. AI identifies it instantly and 
                delivers verified historical facts with pristine source citations.
              </p>
              
              <div className="mt-auto flex items-center gap-2 text-gold-500 font-medium group-hover:gap-4 transition-all duration-300 relative z-10">
                Start Identification <ArrowRight weight="bold" />
              </div>
            </Link>
          </motion.div>
          
        </div>
      </section>

      {/* Features Section */}
      <section className="relative z-20 w-full py-32 px-6 md:px-12 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-24"
        >
          <h2 className="font-serif text-4xl md:text-5xl font-bold text-white mb-6">Mastering the Elements</h2>
          <p className="text-dark-300 max-w-2xl mx-auto text-lg">A sophisticated synthesis of machine learning and rigorous historical data.</p>
        </motion.div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-16">
          {[
            { icon: <Stack weight="duotone" />, title: '5-Stage Pipeline', desc: 'Flawless execution from denoising to colorization, leveraging state-of-the-art weights.' },
            { icon: <Brain weight="duotone" />, title: 'Smart Recognition', desc: 'MobileNetV3 architecture delivering 90%+ accuracy across global heritage sites.' },
            { icon: <Books weight="duotone" />, title: 'Grounded RAG', desc: 'Zero hallucinations. Every historical fact is strictly sourced from verified academic texts.' },
            { icon: <Lightning weight="duotone" />, title: 'Sub-15s Inference', desc: 'Highly optimized tensor operations yielding near-instantaneous restoration on any device.' },
          ].map((feature, i) => (
            <motion.div 
              key={i} 
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: i * 0.1 }}
              className="flex flex-col items-start"
            >
              <div className="text-3xl text-gold-400 mb-6 bg-white/5 p-4 rounded-2xl border border-white/10 shadow-lg">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold mb-3 text-white tracking-wide">{feature.title}</h3>
              <p className="text-sm text-dark-300 leading-relaxed">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Tech Stack Section */}
      <section className="relative z-20 w-full py-32 px-6 md:px-12 bg-black/30 border-t border-white/5">
        <div className="max-w-7xl mx-auto text-center">
          <motion.h2 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-xs font-bold uppercase tracking-[0.3em] text-dark-400 mb-16"
          >
            Engineering Foundation
          </motion.h2>
          
          <div className="flex flex-wrap justify-center gap-12 md:gap-20 opacity-60 grayscale hover:grayscale-0 transition-all duration-700">
            {[
              { icon: <CodeBlock weight="fill" />, name: 'FastAPI' },
              { icon: <Wrench weight="fill" />, name: 'PyTorch' },
              { icon: <Atom weight="fill" />, name: 'React' },
              { icon: <MagnifyingGlass weight="fill" />, name: 'FAISS' },
              { icon: <Cpu weight="fill" />, name: 'LLama' },
              { icon: <Image weight="fill" />, name: 'Real-ESRGAN' },
            ].map((tech, i) => (
              <div key={i} className="flex flex-col items-center gap-3 text-white hover:text-gold-400 hover:scale-110 transition-all duration-300 cursor-default">
                <div className="text-4xl">{tech.icon}</div>
                <span className="text-xs font-semibold tracking-wider">{tech.name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </motion.div>
  );
}
