import { useEffect, useState, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { Send, Sparkles, ChevronDown, ChevronRight, Database } from 'lucide-react';
import { datasetsAPI } from '../lib/api';
import { conversationsAPI } from '../lib/conversationsAPI';
import { Button } from '../components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import ChartRenderer from '../components/ChartRenderer';

interface Message {
    role: 'user' | 'assistant';
    content: any;
}

export default function AnalyticsPage() {
    const location = useLocation();
    const [datasets, setDatasets] = useState<any[]>([]);
    const [selectedDataset, setSelectedDataset] = useState<number | null>(location.state?.datasetId || null);
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    const [currentConversation, setCurrentConversation] = useState<any>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        loadDatasets();
    }, []);

    useEffect(() => {
        if (selectedDataset && !currentConversation) {
            createConversation();
        }
    }, [selectedDataset]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadDatasets = async () => {
        try {
            const response = await datasetsAPI.list();
            setDatasets(response.data);
            if (response.data.length > 0 && !selectedDataset) {
                setSelectedDataset(response.data[0].id);
            }
        } catch (error) {
            console.error('Error loading datasets:', error);
        }
    };

    const createConversation = async () => {
        if (!selectedDataset) return;
        try {
            const response = await conversationsAPI.create(selectedDataset);
            setCurrentConversation(response.data);
        } catch (error) {
            console.error('Error creating conversation:', error);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim() || !currentConversation || loading) return;

        const userMessage: Message = { role: 'user', content: query };
        setMessages(prev => [...prev, userMessage]);
        const userQuery = query;
        setQuery('');
        setLoading(true);

        try {
            const response = await conversationsAPI.sendMessage(currentConversation.id, userQuery);
            const messageData = response.data;

            // Map backend response to Camel.ai structure
            const assistantMessage: Message = {
                role: 'assistant',
                content: {
                    // CamelAI-grade fields from backend
                    understanding: messageData.query_data?.understanding,
                    approach: messageData.query_data?.approach,
                    exploratorySteps: messageData.query_data?.exploratory_steps,

                    // Direct answer from insights
                    directAnswer: messageData.content || "Analysis complete.",

                    // SQL and data
                    sql: messageData.query_data?.generated_sql,
                    resultData: messageData.query_data?.result_data,
                    columns: messageData.query_data?.columns,

                    // Visualization
                    visualization: messageData.query_data?.visualization ? {
                        type: messageData.query_data.visualization.type,
                        xAxis: messageData.query_data.visualization.x_axis,
                        yAxis: messageData.query_data.visualization.y_axis,
                        data: messageData.query_data.result_data,
                        columns: messageData.query_data.columns
                    } : null,

                    // Processing steps for explanation
                    processingSteps: messageData.processing_steps,
                    executionTime: messageData.query_data?.execution_time_ms
                }
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error: any) {
            console.error('Error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: {
                    directAnswer: error.response?.data?.detail || 'Error processing query',
                    error: true
                }
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handlePromptClick = (prompt: string) => {
        setQuery(prompt);
        // Auto-submit
        setTimeout(() => {
            const form = document.querySelector('form');
            form?.requestSubmit();
        }, 100);
    };

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto">
                <div className="max-w-4xl mx-auto px-6 py-8">
                    <AnimatePresence mode="popLayout">
                        {messages.length === 0 ? (
                            <EmptyState
                                onSelectPrompt={handlePromptClick}
                                hasDataset={!!selectedDataset}
                            />
                        ) : (
                            messages.map((message, idx) => (
                                <MessageBubble key={idx} message={message} />
                            ))
                        )}
                    </AnimatePresence>

                    {loading && <TypingIndicator />}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Bar - Fixed at Bottom */}
            <div className="border-t border-border bg-card/50 backdrop-blur-sm">
                <div className="max-w-4xl mx-auto px-6 py-4">
                    <form onSubmit={handleSubmit} className="relative">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Ask about trends, comparisons, anomalies..."
                            disabled={loading || !selectedDataset}
                            className="w-full px-5 py-3.5 pr-14 bg-muted border border-border rounded-xl text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 transition-all disabled:opacity-50"
                        />
                        <Button
                            type="submit"
                            size="sm"
                            disabled={loading || !query.trim() || !selectedDataset}
                            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg bg-accent hover:bg-accent/90"
                        >
                            <Send className="w-4 h-4" />
                        </Button>
                    </form>
                    <p className="text-xs text-center text-muted-foreground mt-2">
                        {selectedDataset ? 'Your data stays private. No training on your data.' : 'Select a dataset to start'}
                    </p>
                </div>
            </div>
        </div>
    );
}

// Empty State Component
function EmptyState({ onSelectPrompt, hasDataset }: { onSelectPrompt: (prompt: string) => void, hasDataset: boolean }) {
    const prompts = [
        "Summarize this dataset with key statistics",
        "What are the main trends this quarter?",
        "Find any unusual patterns or anomalies",
        "Compare performance across categories"
    ];

    if (!hasDataset) {
        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4"
            >
                <Database className="w-16 h-16 text-muted-foreground/30 mb-4" />
                <h2 className="text-xl font-semibold mb-2 text-foreground">No dataset selected</h2>
                <p className="text-sm text-muted-foreground">
                    Select a dataset from the top bar to start analyzing
                </p>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4"
        >
            <div className="mb-8">
                <h1 className="text-3xl font-semibold mb-3 text-foreground">
                    Ask your data anything
                </h1>
                <p className="text-muted-foreground text-sm max-w-md">
                    Powered by your dataset, not assumptions
                </p>
            </div>

            <div className="grid grid-cols-2 gap-3 w-full max-w-2xl">
                {prompts.map((prompt, i) => (
                    <button
                        key={i}
                        onClick={() => onSelectPrompt(prompt)}
                        className="px-4 py-3 text-left text-sm border border-border rounded-lg hover:bg-muted/50 hover:border-accent/30 transition-all text-foreground"
                    >
                        {prompt}
                    </button>
                ))}
            </div>
        </motion.div>
    );
}

// Message Bubble Component
function MessageBubble({ message }: { message: Message }) {
    const [sqlExpanded, setSqlExpanded] = useState(false);
    const [stepsExpanded, setStepsExpanded] = useState(false);

    if (message.role === 'user') {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-end mb-6"
            >
                <div className="max-w-[70%] px-4 py-3 rounded-xl bg-accent/10 text-accent border border-accent/20">
                    <p className="text-sm">{message.content}</p>
                </div>
            </motion.div>
        );
    }

    const content = message.content;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
        >
            <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
                    <Sparkles className="w-4 h-4 text-accent" />
                </div>

                <div className="flex-1 space-y-4">
                    {/* CamelAI-grade: Understanding & Approach */}
                    {content.understanding && (
                        <div className="text-sm text-muted-foreground italic">
                            Understanding: {content.understanding}
                        </div>
                    )}

                    {/* a. Direct Answer */}
                    {content.directAnswer && (
                        <div className="prose prose-invert max-w-none">
                            <ReactMarkdown className="text-foreground text-base leading-relaxed">
                                {content.directAnswer}
                            </ReactMarkdown>
                        </div>
                    )}

                    {/* CamelAI-grade: Exploratory Steps */}
                    {content.exploratorySteps && content.exploratorySteps.length > 0 && (
                        <div className="border border-border rounded-lg overflow-hidden bg-card">
                            <button
                                onClick={() => setStepsExpanded(!stepsExpanded)}
                                className="w-full px-4 py-2.5 flex items-center justify-between text-sm text-muted-foreground hover:bg-muted/50 transition-colors"
                            >
                                <span className="font-medium">Exploratory Analysis ({content.exploratorySteps.length} steps)</span>
                                {stepsExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                            </button>
                            {stepsExpanded && (
                                <div className="px-4 py-3 border-t border-border space-y-3">
                                    {content.exploratorySteps.map((step: any, i: number) => (
                                        <div key={i} className="text-xs">
                                            <div className="font-medium text-foreground mb-1">{step.question}</div>
                                            <div className="text-muted-foreground">{step.finding}</div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* b. Generated SQL (Collapsible) */}
                    {content.sql && (
                        <div className="border border-border rounded-lg overflow-hidden bg-card">
                            <button
                                onClick={() => setSqlExpanded(!sqlExpanded)}
                                className="w-full px-4 py-2.5 flex items-center justify-between text-sm text-muted-foreground hover:bg-muted/50 transition-colors"
                            >
                                <span className="font-medium">Generated SQL</span>
                                {sqlExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                            </button>
                            {sqlExpanded && (
                                <div className="px-4 py-3 border-t border-border">
                                    <pre className="text-xs text-foreground overflow-x-auto">
                                        <code>{content.sql}</code>
                                    </pre>
                                </div>
                            )}
                        </div>
                    )}

                    {/* c. Result Table */}
                    {content.resultData && content.resultData.length > 0 && (
                        <div className="border border-border rounded-lg overflow-hidden">
                            <div className="px-4 py-2 bg-muted/30 border-b border-border">
                                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                    Results ({content.resultData.length} rows)
                                </span>
                            </div>
                            <div className="overflow-x-auto max-h-96">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr>
                                            {content.columns?.map((col: string) => (
                                                <th key={col}>
                                                    {col}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {content.resultData.slice(0, 100).map((row: any, i: number) => (
                                            <tr key={i}>
                                                {content.columns?.map((col: string) => (
                                                    <td key={col}>
                                                        {typeof row[col] === 'number' ? row[col].toLocaleString() : row[col]}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* d. Visualization */}
                    {content.visualization && content.visualization.data && content.visualization.data.length > 0 && (
                        <div className="border border-border rounded-lg p-4 bg-card">
                            <ChartRenderer config={content.visualization} />
                        </div>
                    )}

                    {/* Execution time */}
                    {content.executionTime && (
                        <div className="text-xs text-muted-foreground">
                            Executed in {content.executionTime}ms
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

// Typing Indicator
function TypingIndicator() {
    return (
        <div className="flex gap-3 mb-8">
            <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4 text-accent" />
            </div>
            <div className="flex items-center gap-1 px-4 py-3">
                {[0, 1, 2].map((i) => (
                    <div
                        key={i}
                        className="w-2 h-2 rounded-full bg-muted-foreground"
                        style={{
                            animation: 'typing-bounce 1.4s ease-in-out infinite',
                            animationDelay: `${i * 0.2}s`
                        }}
                    />
                ))}
            </div>
        </div>
    );
}
