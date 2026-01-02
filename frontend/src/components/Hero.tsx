import { Link } from 'react-router-dom';
import { Button } from './ui/button';
import { ArrowRight, BarChart3, BrainCircuit, Sparkles } from 'lucide-react';
import { motion, useInView } from 'framer-motion';
import { useRef, useEffect, useState } from 'react';

export default function Hero() {
    const ref = useRef(null);
    const isInView = useInView(ref, { once: true });
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            setMousePosition({ x: e.clientX, y: e.clientY });
        };
        window.addEventListener('mousemove', handleMouseMove);
        return () => window.removeEventListener('mousemove', handleMouseMove);
    }, []);

    // Floating orbs data
    const orbs = [
        { size: 400, x: 20, y: 10, delay: 0, duration: 20 },
        { size: 300, x: 70, y: 20, delay: 2, duration: 25 },
        { size: 200, x: 50, y: 60, delay: 4, duration: 18 },
        { size: 150, x: 85, y: 70, delay: 1, duration: 22 },
    ];

    return (
        <div ref={ref} className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20 pt-[120px] pb-[80px]">
            {/* Animated Gradient Background */}
            <div className="absolute inset-0 animated-gradient-subtle opacity-60 -z-10" />
            
            {/* Floating Orbs */}
            {orbs.map((orb, i) => (
                <motion.div
                    key={i}
                    className="absolute rounded-full blur-3xl opacity-20"
                    style={{
                        width: orb.size,
                        height: orb.size,
                        left: `${orb.x}%`,
                        top: `${orb.y}%`,
                        background: i % 2 === 0 
                            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                            : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                    }}
                    animate={{
                        y: [0, -30, 0],
                        x: [0, 20, 0],
                        scale: [1, 1.1, 1],
                    }}
                    transition={{
                        duration: orb.duration,
                        delay: orb.delay,
                        repeat: Infinity,
                        ease: "easeInOut",
                    }}
                />
            ))}

            {/* Subtle Grid Pattern */}
            <div className="absolute inset-0 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,#000_70%,transparent_100%)] -z-10" />

            {/* Mouse Follow Glow */}
            <motion.div
                className="absolute w-96 h-96 rounded-full blur-3xl opacity-10 pointer-events-none -z-10"
                style={{
                    background: 'radial-gradient(circle, #667eea 0%, transparent 70%)',
                }}
                animate={{
                    x: mousePosition.x - 192,
                    y: mousePosition.y - 192,
                }}
                transition={{
                    type: "spring",
                    damping: 30,
                    stiffness: 200,
                }}
            />

            <div className="container px-4 md:px-6 relative z-10">
                <div className="flex flex-col items-center text-center space-y-10">
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: isInView ? 1 : 0, y: isInView ? 0 : 10 }}
                        transition={{ duration: 0.5 }}
                        className="inline-flex items-center rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold bg-white/80 backdrop-blur-sm text-slate-600 shadow-lg shimmer"
                    >
                        <Sparkles className="mr-2 h-3.5 w-3.5 text-purple-600" />
                        <span>Universal Analytical Intelligence</span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: isInView ? 1 : 0, y: isInView ? 0 : 20 }}
                        transition={{ duration: 0.6, delay: 0.1 }}
                        className="text-5xl md:text-8xl font-bold tracking-tight max-w-5xl leading-[1.1]"
                    >
                        <span className="text-slate-900">Talk to your data. </span>
                        <br />
                        <span className="gradient-text">Get narratives.</span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: isInView ? 1 : 0, y: isInView ? 0 : 20 }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className="text-lg md:text-xl text-slate-500 max-w-2xl leading-relaxed"
                    >
                        The AI analyst that lives in your workspace. Connect any dataset, ask a question in plain English, and get executive-ready reports in seconds.
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: isInView ? 1 : 0, y: isInView ? 0 : 20 }}
                        transition={{ duration: 0.6, delay: 0.3 }}
                        className="flex flex-col sm:flex-row gap-4 w-full justify-center px-4"
                    >
                        <Link to="/login" className="w-full sm:w-auto group">
                            <Button 
                                size="lg" 
                                className="w-full sm:w-auto text-base h-14 px-10 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 shadow-xl shadow-purple-200 transition-all font-bold relative overflow-hidden group"
                            >
                                <span className="relative z-10 flex items-center">
                                    Get Started Free
                                    <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                                </span>
                                <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-blue-400 opacity-0 group-hover:opacity-20 transition-opacity" />
                            </Button>
                        </Link>
                        <Link to="#features" className="w-full sm:w-auto group">
                            <Button 
                                variant="outline" 
                                size="lg" 
                                className="w-full sm:w-auto text-base h-14 px-10 rounded-xl glass hover:bg-white/90 transition-all font-semibold text-slate-600 border-slate-200 hover:border-purple-200 hover:shadow-lg"
                            >
                                View Demo
                            </Button>
                        </Link>
                    </motion.div>

                    {/* Enhanced UI Preview */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: isInView ? 1 : 0, scale: isInView ? 1 : 0.98 }}
                        transition={{ duration: 0.8, delay: 0.4 }}
                        className="relative w-full max-w-6xl mt-20 mx-auto"
                    >
                        <div className="relative rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden aspect-[16/10] md:aspect-[21/10] flex flex-col group hover:shadow-purple-200/50 hover:border-purple-200 transition-all duration-500">
                            {/* Window Header */}
                            <div className="h-10 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-purple-50/30 flex items-center px-4 gap-2">
                                <div className="w-2.5 h-2.5 rounded-full bg-red-400 group-hover:bg-red-500 transition-colors" />
                                <div className="w-2.5 h-2.5 rounded-full bg-yellow-400 group-hover:bg-yellow-500 transition-colors" />
                                <div className="w-2.5 h-2.5 rounded-full bg-green-400 group-hover:bg-green-500 transition-colors" />
                            </div>

                            <div className="flex-1 grid grid-cols-12 gap-px bg-slate-100">
                                {/* Mock Sidebar */}
                                <motion.div 
                                    className="col-span-3 bg-white p-6 space-y-6"
                                    whileHover={{ backgroundColor: 'rgba(248, 250, 252, 0.5)' }}
                                    transition={{ duration: 0.3 }}
                                >
                                    <div className="space-y-4">
                                        <motion.div 
                                            className="h-4 w-2/3 bg-gradient-to-r from-slate-100 to-purple-100 rounded"
                                            whileHover={{ scale: 1.02 }}
                                        />
                                        <motion.div 
                                            className="h-4 w-full bg-gradient-to-r from-slate-100 to-blue-100 rounded"
                                            whileHover={{ scale: 1.02 }}
                                        />
                                        <motion.div 
                                            className="h-4 w-3/4 bg-gradient-to-r from-slate-100 to-purple-100 rounded"
                                            whileHover={{ scale: 1.02 }}
                                        />
                                    </div>
                                    <div className="pt-8 space-y-4 border-t border-slate-50">
                                        <motion.div 
                                            className="h-10 w-full glass rounded-lg border border-slate-100"
                                            whileHover={{ scale: 1.05, borderColor: '#c084fc' }}
                                            transition={{ duration: 0.2 }}
                                        />
                                        <motion.div 
                                            className="h-10 w-full glass rounded-lg border border-slate-100"
                                            whileHover={{ scale: 1.05, borderColor: '#60a5fa' }}
                                            transition={{ duration: 0.2 }}
                                        />
                                    </div>
                                </motion.div>

                                {/* Mock Content Area */}
                                <div className="col-span-9 bg-white p-8 space-y-8">
                                    <div className="flex justify-between items-center">
                                        <motion.div 
                                            className="h-8 w-1/3 bg-gradient-to-r from-slate-50 to-purple-50 rounded-lg"
                                            animate={{ opacity: [0.5, 1, 0.5] }}
                                            transition={{ duration: 2, repeat: Infinity }}
                                        />
                                        <motion.div 
                                            className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-600 to-blue-600"
                                            whileHover={{ scale: 1.1, rotate: 180 }}
                                            transition={{ duration: 0.3 }}
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-8">
                                        <motion.div 
                                            className="h-64 rounded-xl border border-slate-100 bg-gradient-to-br from-slate-50 to-purple-50/30 flex items-center justify-center overflow-hidden relative"
                                            whileHover={{ scale: 1.02, borderColor: '#c084fc' }}
                                            transition={{ duration: 0.3 }}
                                        >
                                            <BarChart3 className="w-12 h-12 text-purple-300" />
                                            <motion.div
                                                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                                                animate={{ x: ['-100%', '100%'] }}
                                                transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }}
                                            />
                                        </motion.div>
                                        <motion.div 
                                            className="h-64 rounded-xl border border-slate-100 bg-gradient-to-br from-slate-50 to-blue-50/30 flex items-center justify-center overflow-hidden relative"
                                            whileHover={{ scale: 1.02, borderColor: '#60a5fa' }}
                                            transition={{ duration: 0.3 }}
                                        >
                                            <BrainCircuit className="w-12 h-12 text-blue-300" />
                                            <motion.div
                                                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                                                animate={{ x: ['-100%', '100%'] }}
                                                transition={{ duration: 2, repeat: Infinity, repeatDelay: 1, delay: 0.5 }}
                                            />
                                        </motion.div>
                                    </div>
                                    <motion.div 
                                        className="h-32 glass rounded-xl border border-slate-100 p-6 space-y-4"
                                        whileHover={{ scale: 1.01, backgroundColor: 'rgba(255, 255, 255, 0.9)' }}
                                    >
                                        <motion.div 
                                            className="h-3 w-3/4 bg-slate-200 rounded"
                                            animate={{ width: ['75%', '85%', '75%'] }}
                                            transition={{ duration: 3, repeat: Infinity }}
                                        />
                                        <motion.div 
                                            className="h-3 w-1/2 bg-slate-200 rounded"
                                            animate={{ width: ['50%', '60%', '50%'] }}
                                            transition={{ duration: 3, repeat: Infinity, delay: 0.5 }}
                                        />
                                    </motion.div>
                                </div>
                            </div>
                        </div>

                        {/* Floating Metric with Enhanced Animation */}
                        <motion.div
                            animate={{ 
                                y: [0, -15, 0],
                                rotate: [0, 2, 0, -2, 0]
                            }}
                            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute -right-8 top-1/4 p-6 rounded-2xl glass border border-purple-200 shadow-2xl shadow-purple-200/50 hidden md:block"
                            whileHover={{ scale: 1.05 }}
                        >
                            <div className="space-y-2">
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Confidence Score</p>
                                <div className="flex items-center gap-3">
                                    <motion.span 
                                        className="text-3xl font-bold gradient-text"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ duration: 1, delay: 0.5 }}
                                    >
                                        99.8%
                                    </motion.span>
                                    <div className="w-12 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                        <motion.div 
                                            className="h-full bg-gradient-to-r from-green-400 to-emerald-500"
                                            initial={{ width: 0 }}
                                            animate={{ width: '100%' }}
                                            transition={{ duration: 1.5, delay: 0.6 }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
