import { motion, useScroll, useTransform } from 'framer-motion'
import { Link } from 'react-router-dom'
import Hero from '../components/Hero'
import Features from '../components/Features'
import Pricing from '../components/Pricing'
import Testimonials from '../components/Testimonials'
import FAQ from '../components/FAQ'
import { useAuthStore } from '../store/authStore'
import { Button } from '../components/ui/button'
import { BarChart3, Menu, X } from 'lucide-react'
import { useState } from 'react'

const LandingPage = () => {
    const { isAuthenticated } = useAuthStore()
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const { scrollY } = useScroll()
    const headerBg = useTransform(scrollY, [0, 100], ['rgba(255, 255, 255, 0)', 'rgba(255, 255, 255, 0.9)'])
    const headerBlur = useTransform(scrollY, [0, 100], ['blur(0px)', 'blur(8px)'])

    return (
        <div className="min-h-screen bg-card text-foreground selection:bg-purple-100 scroll-smooth font-sans">
            {/* Header */}
            <motion.header
                style={{ backgroundColor: headerBg, backdropFilter: headerBlur }}
                className="fixed top-0 left-0 right-0 z-50 border-b transition-all duration-300"
                animate={{
                    borderColor: scrollY.get() > 100 ? 'rgba(226, 232, 240, 0.8)' : 'transparent'
                }}
            >
                <div className="container mx-auto px-4 h-20 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-2 group">
                        <motion.div
                            className="w-9 h-9 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center shadow-lg group-hover:shadow-purple-300 transition-all"
                            whileHover={{ scale: 1.1, rotate: 5 }}
                            transition={{ type: "spring", stiffness: 400 }}
                        >
                            <BarChart3 className="w-5 h-5 text-white" />
                        </motion.div>
                        <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent">Antigravity</span>
                    </Link>

                    {/* Desktop Nav */}
                    <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
                        <motion.a
                            href="#features"
                            className="hover:text-foreground transition-colors relative group"
                            whileHover={{ y: -2 }}
                        >
                            Features
                            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-purple-600 to-blue-600 group-hover:w-full transition-all duration-300" />
                        </motion.a>
                        <motion.a
                            href="#testimonials"
                            className="hover:text-foreground transition-colors relative group"
                            whileHover={{ y: -2 }}
                        >
                            Testimonials
                            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-purple-600 to-blue-600 group-hover:w-full transition-all duration-300" />
                        </motion.a>
                        <motion.a
                            href="#pricing"
                            className="hover:text-foreground transition-colors relative group"
                            whileHover={{ y: -2 }}
                        >
                            Pricing
                            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-purple-600 to-blue-600 group-hover:w-full transition-all duration-300" />
                        </motion.a>
                        {isAuthenticated ? (
                            <Link to="/dashboard">
                                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                    <Button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 rounded-lg h-10 px-6 font-semibold shadow-lg shadow-purple-200 overflow-hidden transition-all">
                                        Go to Dashboard
                                    </Button>
                                </motion.div>
                            </Link>
                        ) : (
                            <div className="flex items-center gap-4">
                                <motion.div whileHover={{ y: -2 }}>
                                    <Link to="/login" className="hover:text-foreground transition-colors">Login</Link>
                                </motion.div>
                                <Link to="/get-started">
                                    <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                        <Button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 rounded-lg h-10 px-6 font-semibold shadow-lg shadow-purple-200 overflow-hidden transition-all">
                                            Get Started
                                        </Button>
                                    </motion.div>
                                </Link>
                            </div>
                        )}
                    </nav>

                    {/* Mobile Toggle */}
                    <motion.button
                        className="md:hidden p-2 text-foreground hover:bg-slate-100 rounded-lg transition-colors"
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        whileTap={{ scale: 0.9 }}
                    >
                        {isMenuOpen ? <X /> : <Menu />}
                    </motion.button>
                </div>

                {/* Mobile Menu */}
                {isMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -20, height: 0 }}
                        animate={{ opacity: 1, y: 0, height: 'auto' }}
                        exit={{ opacity: 0, y: -20, height: 0 }}
                        className="md:hidden absolute top-20 left-0 right-0 glass border-b border-border p-6 flex flex-col gap-4 shadow-2xl"
                    >
                        <motion.a
                            href="#features"
                            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2"
                            onClick={() => setIsMenuOpen(false)}
                            whileHover={{ x: 5 }}
                        >
                            Features
                        </motion.a>
                        <motion.a
                            href="#testimonials"
                            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2"
                            onClick={() => setIsMenuOpen(false)}
                            whileHover={{ x: 5 }}
                        >
                            Testimonials
                        </motion.a>
                        <motion.a
                            href="#pricing"
                            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2"
                            onClick={() => setIsMenuOpen(false)}
                            whileHover={{ x: 5 }}
                        >
                            Pricing
                        </motion.a>
                        <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent my-2" />
                        <Link to="/login" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2" onClick={() => setIsMenuOpen(false)}>
                            Login
                        </Link>
                        <Link to="/get-started" onClick={() => setIsMenuOpen(false)}>
                            <Button className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg py-3 h-auto font-bold shadow-lg">
                                Get Started
                            </Button>
                        </Link>
                    </motion.div>
                )}
            </motion.header>

            <main>
                <Hero />
                <div id="features" className="scroll-mt-20">
                    <Features />
                </div>
                <div id="testimonials" className="scroll-mt-20">
                    <Testimonials />
                </div>
                <div id="pricing" className="scroll-mt-20">
                    <Pricing />
                </div>
                <FAQ />
            </main>

            {/* Footer */}
            <footer className="py-20 bg-gradient-to-br from-slate-50 via-purple-50/20 to-blue-50/20 border-t border-slate-100">
                <div className="container mx-auto px-4">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
                        <div className="col-span-1 md:col-span-2">
                            <div className="flex items-center gap-2 mb-6 text-foreground">
                                <motion.div
                                    className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center"
                                    whileHover={{ scale: 1.1, rotate: 5 }}
                                >
                                    <BarChart3 className="w-5 h-5 text-white" />
                                </motion.div>
                                <span className="text-2xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent">Antigravity</span>
                            </div>
                            <p className="text-muted-foreground max-w-sm mb-8 leading-relaxed">
                                Universal analytical intelligence for modern teams. Transform raw data into executive narratives in seconds.
                            </p>
                            <div className="flex gap-4">
                                <motion.a
                                    href="#"
                                    className="w-9 h-9 rounded-lg glass border border-border flex items-center justify-center hover:border-purple-300 transition-colors shadow-sm"
                                    whileHover={{ scale: 1.1, y: -2 }}
                                >
                                    <svg className="w-4 h-4 text-slate-600" fill="currentColor" viewBox="0 0 24 24"><path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z" /></svg>
                                </motion.a>
                                <motion.a
                                    href="#"
                                    className="w-9 h-9 rounded-lg glass border border-border flex items-center justify-center hover:border-blue-300 transition-colors shadow-sm"
                                    whileHover={{ scale: 1.1, y: -2 }}
                                >
                                    <svg className="w-4 h-4 text-slate-600" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0 0 22 12c0-5.523-4.477-10-10-10z" /></svg>
                                </motion.a>
                            </div>
                        </div>
                        <div>
                            <h4 className="font-bold mb-6 text-xs text-foreground border-b border-border pb-2">Platform</h4>
                            <ul className="space-y-4 text-sm text-muted-foreground">
                                <li>
                                    <motion.a
                                        href="#features"
                                        className="hover:text-purple-600 transition-colors inline-block"
                                        whileHover={{ x: 3 }}
                                    >
                                        Features
                                    </motion.a>
                                </li>
                                <li>
                                    <motion.a
                                        href="#pricing"
                                        className="hover:text-purple-600 transition-colors inline-block"
                                        whileHover={{ x: 3 }}
                                    >
                                        Pricing
                                    </motion.a>
                                </li>
                                <li>
                                    <motion.a
                                        href="#"
                                        className="hover:text-purple-600 transition-colors inline-block"
                                        whileHover={{ x: 3 }}
                                    >
                                        API Keys
                                    </motion.a>
                                </li>
                                <li>
                                    <motion.a
                                        href="#"
                                        className="hover:text-purple-600 transition-colors inline-block"
                                        whileHover={{ x: 3 }}
                                    >
                                        Infrastructure
                                    </motion.a>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-bold mb-6 text-xs text-foreground border-b border-border pb-2">Resources</h4>
                            <ul className="space-y-4 text-sm text-muted-foreground">
                                <li>
                                    <motion.a
                                        href="#"
                                        className="hover:text-purple-600 transition-colors inline-block"
                                        whileHover={{ x: 3 }}
                                    >
                                        System Status
                                    </motion.a>
                                </li>
                                <li>
                                    <motion.a
                                        href="#"
                                        className="hover:text-purple-600 transition-colors inline-block"
                                        whileHover={{ x: 3 }}
                                    >
                                        Security
                                    </motion.a>
                                </li>
                                <li>
                                    <motion.a
                                        href="#"
                                        className="hover:text-purple-600 transition-colors inline-block"
                                        whileHover={{ x: 3 }}
                                    >
                                        Privacy
                                    </motion.a>
                                </li>
                                <li>
                                    <motion.a
                                        href="#"
                                        className="hover:text-purple-600 transition-colors inline-block"
                                        whileHover={{ x: 3 }}
                                    >
                                        Terms
                                    </motion.a>
                                </li>
                            </ul>
                        </div>
                    </div>
                    <div className="pt-8 border-t border-border flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-medium text-slate-400">
                        <span>© 2024 Antigravity AI. Independent Analysis.</span>
                        <div className="flex gap-8">
                            <span className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                Operational
                            </span>
                            <span className="gradient-text font-semibold">Powered by Gemini</span>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    )
}

export default LandingPage
