import { motion } from 'framer-motion';

const Testimonials = () => {
    const testimonials = [
        {
            quote: "This platform saved our team 20 hours a week on manual data analysis. The AI insights are scary accurate.",
            author: "Sarah Chen",
            role: "Head of Data at NexaTech",
            avatar: "SC"
        },
        {
            quote: "I can ask questions about my business in plain English and get SQL results instantly. It's a game changer.",
            author: "Marcus Brown",
            role: "Founder of GrowthBox",
            avatar: "MB"
        },
        {
            quote: "The Auto-EDA feature provides visualizations that used to take my analysts days to create. Highly recommend.",
            author: "Elena Rodriguez",
            role: "Product Manager at CloudScale",
            avatar: "ER"
        }
    ];

    return (
        <section id="testimonials" className="py-32 bg-white relative">
            <div className="container mx-auto px-4">
                <div className="max-w-3xl mb-24">
                    <h2 className="text-4xl font-bold text-slate-900 mb-6 tracking-tight">Trusted by engineering teams.</h2>
                    <p className="text-xl text-slate-500 leading-relaxed">
                        Join the fastest-growing startups and enterprises using Antigravity to democratize data intelligence across their entire organization.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                    {testimonials.map((t, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 10 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            viewport={{ once: true }}
                            className="flex flex-col gap-8"
                        >
                            <div className="flex gap-1">
                                {[1, 2, 3, 4, 5].map((star) => (
                                    <svg key={star} className="w-4 h-4 text-slate-900 fill-current" viewBox="0 0 20 20">
                                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                    </svg>
                                ))}
                            </div>
                            <p className="text-lg text-slate-900 font-medium leading-relaxed">
                                "{t.quote}"
                            </p>
                            <div className="flex items-center gap-4 pt-4 border-t border-slate-50">
                                <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-900 border border-slate-200">
                                    {t.avatar}
                                </div>
                                <div>
                                    <div className="font-bold text-sm text-slate-900">{t.author}</div>
                                    <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">{t.role}</div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Testimonials;
