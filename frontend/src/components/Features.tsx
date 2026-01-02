import { Zap, Brain, Database, Lock, Search, BarChart } from 'lucide-react';

const features = [
    {
        icon: <Brain className="w-5 h-5 transition-colors" />,
        title: "Conversational BI",
        description: "Translate complex business questions into recursive SQL and stunning visualizations instantly."
    },
    {
        icon: <BarChart className="w-5 h-5 transition-colors" />,
        title: "Automated EDA",
        description: "Identify outliers, correlations, and distribution patterns without writing a single line of code."
    },
    {
        icon: <Database className="w-5 h-5 transition-colors" />,
        title: "Universal Connectors",
        description: "Native support for Snowflake, BigQuery, and traditional SQL warehouses alongside CSV/Excel."
    },
    {
        icon: <Zap className="w-5 h-5 transition-colors" />,
        title: "Dynamic Insights",
        description: "Build reactive dashboards that adapt as your underlying data evolves through our agentic engine."
    },
    {
        icon: <Search className="w-5 h-5 transition-colors" />,
        title: "Verifiable Logic",
        description: "AI-generated queries are transparent and editable. Zero black-box logic, total analytical control."
    },
    {
        icon: <Lock className="w-5 h-5 transition-colors" />,
        title: "Local Execution",
        description: "Compute happens where your data is. Enterprise-grade security with no external data persistence."
    }
];

export default function Features() {
    return (
        <div id="features" className="py-32 bg-white border-t border-slate-100 relative">
            <div className="container px-4 md:px-6 relative z-10">
                <div className="max-w-3xl mb-24">
                    <h2 className="text-4xl font-bold text-slate-900 mb-6 tracking-tight">Built for the next generation of analysts.</h2>
                    <p className="text-slate-500 text-xl leading-relaxed">
                        Antigravity bypasses traditional BI bottlenecks. We provide the speed of a chatbot with the precision of a veteran data engineering team.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12">
                    {features.map((feature, index) => (
                        <div
                            key={index}
                            className="group flex flex-col items-start gap-4"
                        >
                            <div className="w-10 h-10 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-center transition-all group-hover:bg-slate-900 group-hover:border-slate-900 group-hover:text-white group-hover:shadow-lg group-hover:shadow-slate-200">
                                <div className="group-hover:text-white transition-colors">
                                    {feature.icon}
                                </div>
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-slate-900 mb-2">{feature.title}</h3>
                                <p className="text-slate-500 text-sm leading-relaxed">{feature.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
