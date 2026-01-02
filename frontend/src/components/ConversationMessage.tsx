import { motion } from 'framer-motion';
import { User, Bot, Code, Database, CheckCircle, Loader2 } from 'lucide-react';
import { useState } from 'react';

interface ProcessingStep {
    status: string;
    message: string;
    data?: any;
}

interface ConversationMessageProps {
    role: 'user' | 'assistant';
    content: string;
    queryData?: {
        generated_sql?: string;
        result_data?: any[];
        columns?: string[];
        visualization?: any;
        intent?: string;
        confidence?: number;
        insights?: any;
    };
    processingSteps?: ProcessingStep[];
    timestamp?: string;
}

export default function ConversationMessage({
    role,
    content,
    queryData,
    processingSteps,
    timestamp
}: ConversationMessageProps) {
    const [showSQL, setShowSQL] = useState(false);
    const [showData, setShowData] = useState(false);

    const isUser = role === 'user';

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-6`}
        >
            {/* Avatar */}
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isUser ? 'bg-gradient-to-br from-purple-600 to-blue-600' : 'bg-gradient-to-br from-slate-700 to-slate-900'
                }`}>
                {isUser ? (
                    <User className="w-4 h-4 text-white" />
                ) : (
                    <Bot className="w-4 h-4 text-white" />
                )}
            </div>

            {/* Message Content */}
            <div className={`flex-1 max-w-3xl ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-2`}>
                {/* Main Message Bubble */}
                <div className={`rounded-2xl px-4 py-3 ${isUser
                        ? 'bg-gradient-to-br from-purple-600 to-blue-600 text-white ml-auto'
                        : 'glass border border-border'
                    }`}>
                    <p className={`text-sm ${isUser ? 'text-white' : 'text-foreground'} whitespace-pre-wrap`}>
                        {content}
                    </p>
                </div>

                {/* Processing Steps (for assistant messages) */}
                {!isUser && processingSteps && processingSteps.length > 0 && (
                    <div className="w-full space-y-2 mt-2">
                        {processingSteps.map((step, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.1 }}
                                className="flex items-center gap-2 text-xs text-muted-foreground"
                            >
                                {step.status === 'complete' ? (
                                    <CheckCircle className="w-3 h-3 text-green-500" />
                                ) : step.status === 'error' ? (
                                    <span className="w-3 h-3 rounded-full bg-red-500" />
                                ) : (
                                    <Loader2 className="w-3 h-3 animate-spin text-blue-500" />
                                )}
                                <span>{step.message}</span>
                            </motion.div>
                        ))}
                    </div>
                )}

                {/* SQL Code Block (collapsible) */}
                {!isUser && queryData?.generated_sql && (
                    <div className="w-full mt-2">
                        <button
                            onClick={() => setShowSQL(!showSQL)}
                            className="flex items-center gap-2 text-xs text-muted-foreground hover:text-slate-700 transition-colors"
                        >
                            <Database className="w-3 h-3" />
                            <span>{showSQL ? 'Hide' : 'Show'} Generated SQL</span>
                        </button>

                        {showSQL && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                className="mt-2 rounded-lg bg-slate-900 p-3 overflow-hidden"
                            >
                                <div className="flex items-center gap-2 mb-2">
                                    <Code className="w-3 h-3 text-green-400" />
                                    <span className="text-xs text-green-400 font-mono">SQL</span>
                                </div>
                                <pre className="text-xs text-slate-300 font-mono overflow-x-auto">
                                    <code>{queryData.generated_sql}</code>
                                </pre>
                            </motion.div>
                        )}
                    </div>
                )}

                {/* Data Table (collapsible) */}
                {!isUser && queryData?.result_data && queryData.result_data.length > 0 && (
                    <div className="w-full mt-2">
                        <button
                            onClick={() => setShowData(!showData)}
                            className="flex items-center gap-2 text-xs text-muted-foreground hover:text-slate-700 transition-colors"
                        >
                            <span>{showData ? 'Hide' : 'Show'} Data ({queryData.result_data.length} rows)</span>
                        </button>

                        {showData && queryData.columns && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                className="mt-2 rounded-lg border border-border overflow-hidden"
                            >
                                <div className="overflow-x-auto max-h-64">
                                    <table className="w-full text-xs">
                                        <thead className="bg-muted border-b border-border">
                                            <tr>
                                                {queryData.columns.map((col, i) => (
                                                    <th key={i} className="px-3 py-2 text-left font-semibold text-slate-700">
                                                        {col}
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {queryData.result_data.slice(0, 10).map((row, i) => (
                                                <tr key={i} className="border-b border-slate-100 hover:bg-muted">
                                                    {queryData.columns!.map((col, j) => (
                                                        <td key={j} className="px-3 py-2 text-slate-600">
                                                            {row[col] !== null && row[col] !== undefined ? String(row[col]) : 'N/A'}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                {queryData.result_data.length > 10 && (
                                    <div className="px-3 py-2 bg-muted text-xs text-muted-foreground text-center border-t border-border">
                                        Showing 10 of {queryData.result_data.length} rows
                                    </div>
                                )}
                            </motion.div>
                        )}
                    </div>
                )}

                {/* Timestamp */}
                {timestamp && (
                    <span className="text-xs text-slate-400 mt-1">
                        {new Date(timestamp).toLocaleTimeString()}
                    </span>
                )}
            </div>
        </motion.div>
    );
}
