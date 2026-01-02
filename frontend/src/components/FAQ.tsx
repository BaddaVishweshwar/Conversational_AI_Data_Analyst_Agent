import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { useState } from 'react';

const FAQ = () => {
    const faqs = [
        {
            question: "How does the AI analysis work?",
            answer: "Antigravity uses high-reasoning LLMs to profile your data architecture. It then decomposes your natural language queries into logical execution trees, writes precise SQL, and generates interpretative narratives."
        },
        {
            question: "Is my data secure?",
            answer: "We employ a compute-at-source paradigm. Your raw data never leaves your environment; only metadata is processed by our agentic engine to maintain maximum security and compliance."
        },
        {
            question: "Can I connect my existing SQL database?",
            answer: "Yes. We offer native drivers for all major cloud warehouses (Snowflake, BigQuery, Redshift) and traditional relational databases (PostgreSQL, MySQL, SQL Server)."
        },
        {
            question: "Do I need to know SQL to use this?",
            answer: "No. Antigravity is designed to be the bridge between technical data and business operators. However, for power users, we provide a full SQL playground and chart overrides."
        }
    ];

    const [openIndex, setOpenIndex] = useState<number | null>(null);

    return (
        <section className="py-32 bg-muted border-t border-slate-100">
            <div className="container mx-auto px-4 max-w-4xl">
                <div className="max-w-2xl mb-24">
                    <h2 className="text-4xl font-bold text-foreground mb-6 tracking-tight">Common questions.</h2>
                    <p className="text-xl text-muted-foreground leading-relaxed">Everything you need to know about the platform and how we handle your analytical infrastructure.</p>
                </div>

                <div className="space-y-4">
                    {faqs.map((faq, index) => (
                        <div key={index} className="rounded-2xl border border-border bg-card overflow-hidden shadow-sm transition-all hover:border-slate-300">
                            <button
                                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                                className="w-full p-8 flex items-center justify-between text-left transition-colors group"
                            >
                                <span className={`text-lg font-bold transition-colors ${openIndex === index ? 'text-foreground' : 'text-slate-600 group-hover:text-foreground'}`}>{faq.question}</span>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${openIndex === index ? 'bg-slate-900 text-white rotate-180' : 'bg-muted text-slate-400'}`}>
                                    <ChevronDown className="w-4 h-4" />
                                </div>
                            </button>
                            <AnimatePresence>
                                {openIndex === index && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.3, ease: "easeInOut" }}
                                    >
                                        <div className="p-8 pt-0 text-muted-foreground leading-relaxed border-t border-slate-50">
                                            {faq.answer}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default FAQ;
