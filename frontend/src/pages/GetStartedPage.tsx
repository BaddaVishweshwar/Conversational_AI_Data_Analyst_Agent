import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { BarChart3, CheckCircle2, ArrowRight } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { GoogleLogin } from '@react-oauth/google'
import { useToast } from '../hooks/use-toast'

const GetStartedPage = () => {
    const { googleLogin } = useAuthStore()
    const { toast } = useToast()

    const handleGoogleSuccess = async (credentialResponse: any) => {
        try {
            await googleLogin(credentialResponse.credential)
            toast({
                title: "Welcome aboard",
                description: "You've successfully signed in to Antigravity.",
            })
        } catch (error) {
            toast({
                title: "Authentication failed",
                description: "There was an error signing in with Google.",
                variant: "destructive",
            })
        }
    }

    const steps = [
        {
            title: "Connect your data source",
            description: "Link your database, CSVs, or API endpoints. Our engine handles the structural mapping automatically.",
            icon: <div className="w-10 h-10 rounded-full bg-[#f3f4f6] flex items-center justify-center text-slate-900 font-bold border border-slate-200">1</div>
        },
        {
            title: "Configure AI Expertise",
            description: "Define the business context and objectives. Our RAG engine builds a semantic index of your domain.",
            icon: <div className="w-10 h-10 rounded-full bg-[#f3f4f6] flex items-center justify-center text-slate-900 font-bold border border-slate-200">2</div>
        },
        {
            title: "Unlock Instant Insights",
            description: "Chat with your data, generate SQL, and build dashboards in seconds without writing a line of code.",
            icon: <div className="w-10 h-10 rounded-full bg-[#f3f4f6] flex items-center justify-center text-slate-900 font-bold border border-slate-200">3</div>
        }
    ]

    return (
        <div className="min-h-screen bg-[#fafafa] flex flex-col font-sans selection:bg-black selection:text-white">
            {/* Minimalist Header */}
            <header className="px-8 py-6 flex items-center justify-between max-w-7xl mx-auto w-full">
                <Link to="/" className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-black rounded flex items-center justify-center">
                        <BarChart3 className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-xl font-bold tracking-tight text-slate-900">Antigravity</span>
                </Link>
                <div className="hidden sm:flex items-center gap-6 text-sm font-medium text-slate-500">
                    <Link to="/#features" className="hover:text-black transition-colors">How it works</Link>
                    <Link to="/login" className="px-4 py-2 border border-slate-200 rounded-lg hover:border-slate-400 hover:bg-white text-slate-900 transition-all">Log in</Link>
                </div>
            </header>

            <main className="flex-1 flex flex-col items-center justify-center px-6 py-20 bg-white">
                <div className="max-w-4xl w-full">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                        className="text-center mb-16"
                    >
                        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6 tracking-tight">
                            Start building with Antigravity AI.
                        </h1>
                        <p className="text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
                            Join over 500+ teams automating their business analytics. No complex setup, no upfront costs.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 gap-16 items-start">
                        {/* Steps Section */}
                        <div className="space-y-12">
                            {steps.map((step, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.2 + index * 0.1 }}
                                    className="flex gap-6"
                                >
                                    <div className="shrink-0">
                                        {step.icon}
                                    </div>
                                    <div className="space-y-2">
                                        <h3 className="font-bold text-slate-900 text-lg">{step.title}</h3>
                                        <p className="text-slate-500 leading-relaxed text-sm">
                                            {step.description}
                                        </p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>

                        {/* Sign-in Card */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.5 }}
                            className="bg-white border-2 border-slate-100 rounded-3xl p-10 shadow-2xl shadow-slate-200/50"
                        >
                            <div className="mb-8 p-4 bg-emerald-50 rounded-2xl border border-emerald-100 flex items-start gap-3">
                                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                                <div className="text-sm text-emerald-900 leading-snug">
                                    <strong>Private & Secure</strong>: Your data never leaves your environment. We only manage the semantic mapping layer.
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="flex flex-col gap-4">
                                    <p className="text-sm font-bold text-slate-400 uppercase tracking-widest text-center">Step 1: Authenticate</p>
                                    <div className="flex justify-center border border-slate-200 rounded-xl p-4 bg-slate-50/50 hover:bg-slate-50 transition-colors">
                                        <GoogleLogin
                                            onSuccess={handleGoogleSuccess}
                                            onError={() => console.log('Login Failed')}
                                            useOneTap
                                            shape="pill"
                                            theme="outline"
                                            text="continue_with"
                                        />
                                    </div>
                                </div>

                                <div className="relative">
                                    <div className="absolute inset-0 flex items-center">
                                        <span className="w-full border-t border-slate-100" />
                                    </div>
                                    <div className="relative flex justify-center text-xs uppercase">
                                        <span className="bg-white px-2 text-slate-400 font-medium">Or Use Email</span>
                                    </div>
                                </div>

                                <Link
                                    to="/register"
                                    className="flex items-center justify-center w-full px-6 py-4 bg-black text-white rounded-xl font-bold hover:bg-slate-800 transition-all gap-2 group"
                                >
                                    Create Account
                                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </Link>

                                <p className="text-xs text-center text-slate-400 leading-relaxed">
                                    By continuing, you agree to our <a href="#" className="underline hover:text-slate-900">Terms</a> and <a href="#" className="underline hover:text-slate-900">Privacy Policy</a>.
                                </p>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </main>

            {/* Founder note / Social proof */}
            <section className="bg-[#fafafa] py-20">
                <div className="max-w-4xl mx-auto px-6">
                    <div className="bg-white border border-slate-200 p-8 md:p-12 rounded-2xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-slate-50 -mr-16 -mt-16 rounded-full" />
                        <p className="text-slate-700 italic text-lg leading-relaxed mb-8 relative z-10">
                            "Most analytics tools focus on fancy charts. At Antigravity, we focus on the bridge between data and decisions. We're building the infrastructure for the next generation of data-literate companies."
                        </p>
                        <div className="flex items-center gap-4 relative z-10">
                            <div className="w-12 h-12 rounded-full bg-slate-200 overflow-hidden">
                                <img src="/placeholder-avatar.jpg" alt="Founder" className="w-full h-full object-cover" />
                            </div>
                            <div>
                                <h4 className="font-bold text-slate-900">Alex Rivera</h4>
                                <p className="text-sm text-slate-500">Founder & CEO, Antigravity AI</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <footer className="py-12 border-t border-slate-100 bg-white">
                <div className="container mx-auto px-8 flex flex-col md:flex-row items-center justify-between gap-6 text-sm text-slate-400 font-medium">
                    <span>© 2025 Antigravity AI. All rights reserved.</span>
                    <div className="flex gap-8">
                        <a href="#" className="hover:text-black">Terms</a>
                        <a href="#" className="hover:text-black">Privacy</a>
                        <a href="#" className="hover:text-black">Contact</a>
                    </div>
                </div>
            </footer>
        </div>
    )
}

export default GetStartedPage
