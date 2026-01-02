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
        // Supporting both legacy single object and new list
        visualization?: {
            chart_type: string;
            x_axis?: string;
            y_axis?: string[];
            title?: string;
            description?: string;
        };
        visualizations?: {
            chart_type: string;
            x_axis?: string;
            y_axis?: string[];
            title?: string;
            description?: string;
        }[];
        intent?: {
            intent: string;
            confidence: number;
        };
        interpretation?: {
            title: string;
            main_finding: string;
            outliers: string[];
            trends: string[];
            top_contributors: string[];
            correlations: string[];
        };
        insights?: {
            direct_answer: string;
            what_data_shows: string[];
            why_it_happened: string[];
            business_implications: string[];
            confidence: number;
        };
    };
    processingSteps?: (ProcessingStep | string)[];
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
    // Determine which visualizations to use
    const activeVisualizations = queryData?.visualizations || (queryData?.visualization ? [queryData.visualization] : []);
    const hasViz = activeVisualizations.length > 0 && activeVisualizations[0].chart_type !== 'table';

    // Helper to render specific charts
    const renderChart = (vizConfig: any) => {
        if (!vizConfig || !queryData?.result_data) return null;

        const { chart_type, x_axis, y_axis } = vizConfig;
        const data = queryData.result_data;

        // Common tooltip style
        const CustomTooltip = ({ active, payload, label }: any) => {
            if (active && payload && payload.length) {
                return (
                    <div className="bg-card p-3 border border-border rounded-lg shadow-lg">
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
                            {y_axis?.map((key: string, index: number) => (
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
                            {y_axis?.map((key: string, index: number) => (
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
                                label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey={y_axis?.[0] || 'value'}
                            >
                                {data.map((_entry: any, index: number) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <RechartsTooltip />
                        </RePieChart>
                    </ResponsiveContainer>
                );
            case 'histogram':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={data} barCategoryGap={0}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey={x_axis} tick={{ fontSize: 12 }} />
                            <YAxis tick={{ fontSize: 12 }} />
                            <RechartsTooltip content={<CustomTooltip />} />
                            <Legend />
                            <Bar dataKey={y_axis?.[0] || 'frequency'} fill="#8884d8" name="Frequency" />
                        </BarChart>
                    </ResponsiveContainer>
                );
            case 'scatter':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey={x_axis} />
                            <YAxis />
                            <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                            <Legend />
                            {y_axis?.map((key: string, index: number) => (
                                <Bar key={key} dataKey={key} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </BarChart>
                    </ResponsiveContainer>
                );
            case 'kpi':
            case 'metric_card':
                // Render a simple card for metric/KPI
                const kpiKey = y_axis?.[0] || 'value';
                const kpiValue = data[0]?.[kpiKey];
                return (
                    <div className="flex flex-col items-center justify-center h-full border border-slate-100 rounded-lg p-6 bg-muted">
                        <div className="text-4xl font-bold text-slate-800">{typeof kpiValue === 'number' ? kpiValue.toLocaleString() : kpiValue}</div>
                        <div className="text-sm text-muted-foreground mt-2">{vizConfig.title}</div>
                    </div>
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
                <div className="bg-card rounded-2xl border border-border shadow-sm overflow-hidden">
                    {/* Header: Direct Answer */}
                    <div className="bg-muted/50 p-6 border-b border-slate-100">
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

                            {/* Statistical Analysis (New Layer) */}
                            {queryData.interpretation && (
                                <div className="bg-blue-50/30 rounded-xl p-4 border border-blue-100/50">
                                    <h4 className="text-xs font-semibold text-blue-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                                        <TrendingUp className="w-4 h-4" />
                                        Statistical Findings
                                    </h4>
                                    <div className="space-y-2">
                                        <p className="text-sm font-medium text-slate-800">
                                            {queryData.interpretation.main_finding}
                                        </p>
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {queryData.interpretation.outliers.map((o, i) => (
                                                <span key={i} className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-md border border-red-200">
                                                    {o}
                                                </span>
                                            ))}
                                            {queryData.interpretation.trends.map((t, i) => (
                                                <span key={i} className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-md border border-green-200">
                                                    {t}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Visualization Grid (Multi-Chart) */}
                            {hasViz && (
                                <div className="space-y-4">
                                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                        <TrendingUp className="w-4 h-4" />
                                        Visual Analysis
                                    </h4>
                                    <div className={`grid gap-4 ${activeVisualizations.length > 1 ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}>
                                        {activeVisualizations.map((viz, idx) => (
                                            <div key={idx} className={`bg-card border border-slate-100 rounded-xl p-4 shadow-sm ${viz.chart_type === 'kpi' ? 'md:col-span-1' : 'md:col-span-2'}`}>
                                                {viz.title && <h5 className="text-sm font-medium text-slate-700 mb-2">{viz.title}</h5>}
                                                {viz.description && <p className="text-xs text-muted-foreground mb-4">{viz.description}</p>}
                                                {renderChart(viz)}
                                            </div>
                                        ))}
                                    </div>
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
                                            <li key={i} className="flex items-start gap-3 text-sm text-slate-700 bg-muted p-3 rounded-lg">
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
                            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted-foreground bg-card border border-border rounded-full hover:bg-muted transition-all"
                        >
                            {showSteps ? <ChevronUp className="w-3 h-3" /> : <Loader2 className="w-3 h-3" />}
                            {showSteps ? 'Hide Process' : 'Show Process'}
                        </button>
                    )}

                    {queryData?.generated_sql && (
                        <button
                            onClick={() => setShowSQL(!showSQL)}
                            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted-foreground bg-card border border-border rounded-full hover:bg-muted transition-all"
                        >
                            {showSQL ? <ChevronUp className="w-3 h-3" /> : <Code className="w-3 h-3" />}
                            {showSQL ? 'Hide SQL' : 'Show SQL'}
                        </button>
                    )}

                    {queryData?.result_data && (
                        <button
                            onClick={() => setShowData(!showData)}
                            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted-foreground bg-card border border-border rounded-full hover:bg-muted transition-all"
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
                                {processingSteps.map((step, index) => {
                                    const isString = typeof step === 'string';
                                    const message = isString ? step : step.message;
                                    const status = isString ? 'complete' : step.status;

                                    return (
                                        <div key={index} className="flex items-center gap-3 text-xs text-slate-300">
                                            {status === 'complete' ? (
                                                <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0" />
                                            ) : status === 'error' ? (
                                                <div className="w-3 h-3 rounded-full bg-red-400 flex-shrink-0" />
                                            ) : (
                                                <Loader2 className="w-3 h-3 animate-spin text-blue-400 flex-shrink-0" />
                                            )}
                                            <span>{message}</span>
                                        </div>
                                    );
                                })}
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
                            <div className="bg-card border border-border rounded-xl overflow-hidden">
                                <div className="overflow-x-auto max-h-96">
                                    <table className="w-full text-sm">
                                        <thead className="bg-muted border-b border-border">
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
                                                <tr key={i} className="border-b border-slate-100 hover:bg-muted group">
                                                    {queryData.columns?.map((col, j) => (
                                                        <td key={j} className="px-4 py-2.5 text-slate-600 group-hover:text-foreground whitespace-nowrap">
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
