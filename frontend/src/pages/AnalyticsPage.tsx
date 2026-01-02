import { useEffect, useState, useRef } from 'react';
import { Send, Sparkles, ChevronDown, ChevronRight, BarChart3, Table2, MapPin, FileText, Plus } from 'lucide-react';
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
    const [datasets, setDatasets] = useState<any[]>([]);
    const [selectedDataset, setSelectedDataset] = useState<number | null>(null);
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
            setMessages([]);
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

            const assistantMessage: Message = {
                role: 'assistant',
                content: {
                    directAnswer: messageData.content || "Analysis complete.",
                    sql: messageData.query_data?.generated_sql,
                    resultData: messageData.query_data?.result_data,
                    columns: messageData.query_data?.columns,
                    visualization: messageData.query_data?.visualization ? {
                        type: messageData.query_data.visualization.type,
                        xAxis: messageData.query_data.visualization.x_axis,
                        yAxis: messageData.query_data.visualization.y_axis,
                        data: messageData.query_data.result_data,
                        columns: messageData.query_data.columns
                    } : null,
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
    };

    const suggestionChips = [
        { icon: BarChart3, text: 'Compare sales vs ad spend' },
        { icon: Table2, text: 'Join customers with orders' },
        { icon: MapPin, text: 'Find anomalies by region' },
    ];

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto">
                <div className="max-w-4xl mx-auto px-6 py-8">
                    <AnimatePresence mode="popLayout">
                        {messages.length === 0 ? (
                            <EmptyState
                                datasets={datasets}
                                onSelectPrompt={handlePromptClick}
                                suggestionChips={suggestionChips}
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
            <div className="border-t border-border bg-background/95 backdrop-blur-sm">
                <div className="max-w-4xl mx-auto px-6 py-4">
                    <form onSubmit={handleSubmit} className="relative">
                        <textarea
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit(e);
                                }
                            }}
                            placeholder="Ask about trends, comparisons, anomalies..."
                            disabled={loading || !selectedDataset}
                            rows={1}
                            className="w-full px-5 py-3.5 pr-14 bg-muted/50 border border-border rounded-xl text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/20 transition-all resize-none disabled:opacity-50"
                        />
                        <Button
                            type="submit"
                            size="sm"
                            disabled={loading || !query.trim() || !selectedDataset}
                            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg bg-accent hover:bg-accent/90 text-white p-2"
                        >
                            <Send className="w-4 h-4" />
                        </Button>
                    </form>
                    <p className="text-xs text-center text-muted-foreground mt-2">
                        Shift+Enter to add a line
                    </p>
                </div>
            </div>
        </div>
    );
}

// Empty State Component
function EmptyState({ datasets, onSelectPrompt, suggestionChips }: any) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4"
        >
            <div className="mb-8">
                <h1 className="text-4xl font-semibold mb-4 text-foreground">
                    Ask your data anything
                </h1>
                <p className="text-muted-foreground text-base mb-2">
                    You're analyzing {datasets.length} dataset{datasets.length !== 1 ? 's' : ''}.
                </p>
                <p className="text-muted-foreground text-sm">
                    Ask questions across them or focus on one:
                </p>
            </div>

            {/* Suggestion Chips */}
            <div className="flex flex-wrap gap-3 justify-center mb-8 max-w-2xl">
                {suggestionChips.map((chip: any, i: number) => {
                    const Icon = chip.icon;
                    return (
                        <button
                            key={i}
                            onClick={() => onSelectPrompt(chip.text)}
                            className="flex items-center gap-2 px-4 py-2.5 text-sm border border-border rounded-lg hover:bg-muted/50 hover:border-accent/30 transition-all text-foreground bg-card"
                        >
                            <Icon className="w-4 h-4 text-muted-foreground" />
                            <span>{chip.text}</span>
                        </button>
                    );
                })}
            </div>

            {/* Dataset Info Link */}
            {datasets.length > 0 && (
                <button
                    onClick={() => onSelectPrompt(`Show me ${datasets[0].name} info`)}
                    className="flex items-center gap-2 text-sm text-muted-foreground hover:text-accent transition-colors"
                >
                    <FileText className="w-4 h-4" />
                    <span>Show me {datasets[0].name} info</span>
                    <ChevronRight className="w-3 h-3" />
                </button>
            )}
        </motion.div>
    );
}

// Message Bubble Component  
function MessageBubble({ message }: { message: Message }) {
    const [sqlExpanded, setSqlExpanded] = useState(false);

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
                    {content.directAnswer && (
                        <div className="prose prose-invert max-w-none">
                            <ReactMarkdown className="text-foreground text-base leading-relaxed">
                                {content.directAnswer}
                            </ReactMarkdown>
                        </div>
                    )}

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
                                                <th key={col}>{col}</th>
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

                    {content.visualization && content.visualization.data && content.visualization.data.length > 0 && (
                        <div className="border border-border rounded-lg p-4 bg-card">
                            <ChartRenderer config={content.visualization} />
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
