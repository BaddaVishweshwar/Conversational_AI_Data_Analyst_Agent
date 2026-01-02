import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    User, Bot, Code, Database, CheckCircle, Loader2,
    TrendingUp, Lightbulb,
    Target, ArrowRight, ChevronUp, AlertCircle
} from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
    LineChart, Line, PieChart as RePieChart, Pie, Cell
} from 'recharts';

interface ProcessingStep {
    status: string;
    message: string;
    data?: any;
}

interface ConversationMessageV2Props {
    role: 'user' | 'assistant';
    content: string;
    queryData?: {
        generated_sql?: string;
        result_data?: any[];
        columns?: string[];
        visualization?: {
            chart_type: string;
            x_axis?: string;
            y_axis?: string[];
            title?: string;
        };
        intent?: string;
        confidence?: number;
        insights?: {
            direct_answer: string;
            what_data_shows: string[];
            why_it_happened: string[];
            business_implications: string[];
            confidence: number;
        };
    };
    processingSteps?: ProcessingStep[];
    timestamp?: string;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088fe', '#00c49f'];

export default function ConversationMessageV2({
    role,
    content,
    queryData,
    processingSteps,
    timestamp
}: ConversationMessageV2Props) {
    const [showSQL, setShowSQL] = useState(false);
    const [showData, setShowData] = useState(false);
    const [showSteps, setShowSteps] = useState(false);

    const isUser = role === 'user';
    const hasInsights = queryData?.insights;
    const hasViz = queryData?.visualization && queryData.visualization.chart_type !== 'table';

    // Helper to render specific charts
    const renderChart = () => {
        if (!queryData?.visualization || !queryData.result_data) return null;

        const { chart_type, x_axis, y_axis } = queryData.visualization;
        const data = queryData.result_data;

        // Common tooltip style
        const CustomTooltip = ({ active, payload, label }: any) => {
            if (active && payload && payload.length) {
                return (
                    <div className="bg-white p-3 border border-slate-200 rounded-lg shadow-lg">
                        <p className="font-semibold text-slate-700 mb-1">{label}</p>
                        {payload.map((entry: any, index: number) => (
                            <div key={index} className="text-sm text-slate-600">
                                <span style={{ color: entry.color }}>{entry.name}: </span>
                                {typeof entry.value === 'number'
                                    ? entry.value.toLocaleString()
                                    : entry.value}
                            </div>
                        ))}
                    </div>
                );
            }
            return null;
        };

        switch (chart_type) {
            case 'bar':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey={x_axis} tick={{ fontSize: 12 }} />
                            <YAxis tick={{ fontSize: 12 }} />
                            <RechartsTooltip content={<CustomTooltip />} />
                            <Legend />
                            {y_axis?.map((key, index) => (
                                <Bar
                                    key={key}
                                    dataKey={key}
                                    fill={COLORS[index % COLORS.length]}
                                    radius={[4, 4, 0, 0]}
                                />
                            ))}
                        </BarChart>
                    </ResponsiveContainer>
                );
            case 'line':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey={x_axis} tick={{ fontSize: 12 }} />
                            <YAxis tick={{ fontSize: 12 }} />
                            <RechartsTooltip content={<CustomTooltip />} />
                            <Legend />
                            {y_axis?.map((key, index) => (
                                <Line
                                    key={key}
                                    type="monotone"
                                    dataKey={key}
                                    stroke={COLORS[index % COLORS.length]}
                                    strokeWidth={2}
                                    dot={{ r: 4 }}
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                );
            case 'pie':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <RePieChart>
                            <Pie
                                data={data}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey={y_axis?.[0] || 'value'}
                            >
                                {data.map((_entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <RechartsTooltip />
                        </RePieChart>
                    </ResponsiveContainer>
                );
            default:
                return null;
        }
    };

    if (isUser) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-row-reverse gap-3 mb-6"
            >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-md">
                    <User className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gradient-to-br from-purple-600 to-blue-600 text-white px-5 py-3 rounded-2xl rounded-tr-none shadow-md max-w-[80%]">
                    <p className="text-sm">{content}</p>
                    {timestamp && (
                        <span className="text-xs text-purple-200 mt-1 block opacity-70">
                            {new Date(timestamp).toLocaleTimeString()}
                        </span>
                    )}
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-4 mb-8 w-full max-w-5xl mx-auto"
        >
            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center flex-shrink-0 shadow-md mt-1">
                <Bot className="w-4 h-4 text-white" />
            </div>

            <div className="flex-1 space-y-4">
                {/* Main Insight Card */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                    {/* Header: Direct Answer */}
                    <div className="bg-slate-50/50 p-6 border-b border-slate-100">
                        {hasInsights ? (
                            <p className="text-lg font-medium text-slate-800 leading-relaxed">
                                {queryData.insights?.direct_answer}
                            </p>
                        ) : (
                            <p className="text-sm text-slate-800 whitespace-pre-wrap">{content}</p>
                        )}
                    </div>

                    {/* Content Section */}
                    {hasInsights && (
                        <div className="p-6 space-y-8">

                            {/* Visualization */}
                            {hasViz && (
                                <div className="bg-white border border-slate-100 rounded-xl p-4 shadow-sm">
                                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                        <TrendingUp className="w-4 h-4" />
                                        Visual Analysis
                                    </h4>
                                    {renderChart()}
                                </div>
                            )}

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {/* Key Findings */}
                                <div>
                                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                        <Lightbulb className="w-4 h-4" />
                                        Key Findings
                                    </h4>
                                    <ul className="space-y-3">
                                        {queryData.insights?.what_data_shows && queryData.insights.what_data_shows.map((item, i) => (
                                            <li key={i} className="flex items-start gap-3 text-sm text-slate-700 bg-slate-50 p-3 rounded-lg">
                                                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                                                <span>{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* Strategic Implications */}
                                <div>
                                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                        <Target className="w-4 h-4" />
                                        Strategic Recommendations
                                    </h4>
                                    <ul className="space-y-3">
                                        {queryData.insights?.business_implications && queryData.insights.business_implications.map((item, i) => (
                                            <li key={i} className="flex items-start gap-3 text-sm text-slate-700 bg-purple-50/50 p-3 rounded-lg border border-purple-100/50">
                                                <ArrowRight className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                                                <span>{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>

                            {/* Why it happened (Accordion style or simple block) */}
                            {queryData.insights?.why_it_happened && queryData.insights.why_it_happened.length > 0 && (
                                <div className="bg-amber-50/50 rounded-xl p-4 border border-amber-100/50">
                                    <h4 className="text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2 flex items-center gap-2">
                                        <AlertCircle className="w-4 h-4" />
                                        Drivers & Context
                                    </h4>
                                    <div className="space-y-2">
                                        {queryData.insights.why_it_happened.map((item, i) => (
                                            <p key={i} className="text-sm text-slate-700 leading-relaxed">
                                                {item}
                                            </p>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer Controls */}
                <div className="flex flex-wrap items-center gap-3">
                    {processingSteps && processingSteps.length > 0 && (
                        <button
                            onClick={() => setShowSteps(!showSteps)}
                            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-500 bg-white border border-slate-200 rounded-full hover:bg-slate-50 transition-all"
                        >
                            {showSteps ? <ChevronUp className="w-3 h-3" /> : <Loader2 className="w-3 h-3" />}
                            {showSteps ? 'Hide Process' : 'Show Process'}
                        </button>
                    )}

                    {queryData?.generated_sql && (
                        <button
                            onClick={() => setShowSQL(!showSQL)}
                            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-500 bg-white border border-slate-200 rounded-full hover:bg-slate-50 transition-all"
                        >
                            {showSQL ? <ChevronUp className="w-3 h-3" /> : <Code className="w-3 h-3" />}
                            {showSQL ? 'Hide SQL' : 'Show SQL'}
                        </button>
                    )}

                    {queryData?.result_data && (
                        <button
                            onClick={() => setShowData(!showData)}
                            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-500 bg-white border border-slate-200 rounded-full hover:bg-slate-50 transition-all"
                        >
                            {showData ? <ChevronUp className="w-3 h-3" /> : <Database className="w-3 h-3" />}
                            {showData ? 'Hide Data' : `Show Data (${queryData.result_data.length} rows)`}
                        </button>
                    )}
                </div>

                {/* Collapsible Details Sections */}
                <AnimatePresence>
                    {showSteps && processingSteps && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="bg-slate-900 rounded-xl p-4 space-y-3">
                                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Processing Steps</h4>
                                {processingSteps.map((step, index) => (
                                    <div key={index} className="flex items-center gap-3 text-xs text-slate-300">
                                        {step.status === 'complete' ? (
                                            <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0" />
                                        ) : step.status === 'error' ? (
                                            <div className="w-3 h-3 rounded-full bg-red-400 flex-shrink-0" />
                                        ) : (
                                            <Loader2 className="w-3 h-3 animate-spin text-blue-400 flex-shrink-0" />
                                        )}
                                        <span>{step.message}</span>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {showSQL && queryData?.generated_sql && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto">
                                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Generated SQL</h4>
                                <pre className="text-xs text-cyan-300 font-mono">
                                    <code>{queryData.generated_sql}</code>
                                </pre>
                            </div>
                        </motion.div>
                    )}

                    {showData && queryData?.result_data && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                                <div className="overflow-x-auto max-h-96">
                                    <table className="w-full text-sm">
                                        <thead className="bg-slate-50 border-b border-slate-200">
                                            <tr>
                                                {queryData.columns?.map((col, i) => (
                                                    <th key={i} className="px-4 py-3 text-left font-semibold text-slate-700 whitespace-nowrap">
                                                        {col}
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {queryData.result_data.map((row, i) => (
                                                <tr key={i} className="border-b border-slate-100 hover:bg-slate-50 group">
                                                    {queryData.columns?.map((col, j) => (
                                                        <td key={j} className="px-4 py-2.5 text-slate-600 group-hover:text-slate-900 whitespace-nowrap">
                                                            {row[col] !== null ? String(row[col]) : '-'}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}
