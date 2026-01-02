import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

const Pricing = () => {
    const plans = [
        {
            name: "Starter",
            price: "0",
            description: "For individuals and small teams.",
            features: ["Personal Datasets", "Standard AI Agent", "Basic Visualizations", "Query History"],
            cta: "Get Started",
            popular: false
        },
        {
            name: "Pro",
            price: "29",
            description: "Everything for high-growth teams.",
            features: ["Unlimited Datasets", "Advanced AI Agent", "Custom Chart Tuner", "Team Collaboration", "API Access"],
            cta: "Go Pro",
            popular: true
        },
        {
            name: "Enterprise",
            price: "Custom",
            description: "Global infrastructure & security.",
            features: ["Single Sign-On (SSO)", "Dedicated AI Lab", "Audit Logs", "SLA Guarantee", "24/7 Support"],
            cta: "Talk to Sales",
            popular: false
        }
    ];

    return (
        <section id="pricing" className="py-32 bg-muted relative overflow-hidden">
            <div className="container mx-auto px-4 relative z-10">
                <div className="max-w-3xl mb-24">
                    <h2 className="text-4xl font-bold text-foreground mb-6 tracking-tight">Predictable pricing.</h2>
                    <p className="text-xl text-muted-foreground leading-relaxed">
                        Start for free, then scale as your analytical needs grow. No hidden platform fees or per-user taxes.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {plans.map((plan, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            viewport={{ once: true }}
                            className={`relative p-8 rounded-2xl border ${plan.popular
                                ? 'bg-card border-slate-900 shadow-2xl scale-105 z-10'
                                : 'bg-card border-border shadow-sm'
                                }`}
                        >
                            {plan.popular && (
                                <div className="absolute -top-3 left-6 bg-slate-900 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-widest shadow-lg">
                                    Recommended
                                </div>
                            )}

                            <div className="mb-8">
                                <h3 className="text-2xl font-bold text-foreground mb-1">{plan.name}</h3>
                                <div className="flex items-baseline gap-1">
                                    <span className="text-4xl font-bold text-foreground">{plan.price !== "Custom" ? `$${plan.price}` : plan.price}</span>
                                    {plan.price !== "Custom" && <span className="text-slate-400 font-medium">/mo</span>}
                                </div>
                                <p className="text-muted-foreground mt-4 text-sm font-medium leading-relaxed">{plan.description}</p>
                            </div>

                            <div className="space-y-4 mb-10">
                                {plan.features.map((feature, i) => (
                                    <div key={i} className="flex items-center gap-3">
                                        <Check className="w-4 h-4 text-slate-400" />
                                        <span className="text-sm text-slate-600 font-medium">{feature}</span>
                                    </div>
                                ))}
                            </div>

                            <button className={`w-full py-4 rounded-xl font-bold transition-all h-14 ${plan.popular
                                ? 'bg-slate-900 text-white hover:bg-black shadow-lg shadow-slate-200'
                                : 'bg-muted border border-border text-foreground hover:bg-slate-100'
                                }`}>
                                {plan.cta}
                            </button>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Pricing;
