import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Send, Plus, Sparkles, Loader2, ArrowLeft } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { conversationsAPI } from '../lib/conversationsAPI';
import { datasetsAPI } from '../lib/api';
import ConversationMessageV2 from '../components/ConversationMessageV2';
import { Button } from '../components/ui/button';
import { useToast } from '../hooks/use-toast';

interface Message {
    id: number;
    role: 'user' | 'assistant';
    content: string;
    query_data?: any;
    processing_steps?: any[];
    created_at: string;
}

interface Conversation {
    id: number;
    dataset_id: number;
    title: string;
    created_at: string;
    updated_at: string;
    message_count: number;
}

export default function ConversationalAnalyticsPage() {
    const { toast } = useToast();
    const location = useLocation();
    const navigate = useNavigate();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const [datasets, setDatasets] = useState<any[]>([]);
    const [selectedDataset, setSelectedDataset] = useState<number | null>(
        location.state?.datasetId || null
    );
    const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [sending, setSending] = useState(false);

    // Load datasets on mount
    useEffect(() => {
        loadDatasets();
    }, []);

    // Create conversation when dataset is selected
    useEffect(() => {
        if (selectedDataset && !currentConversation) {
            createNewConversation();
        }
    }, [selectedDataset]);

    // Auto-scroll to bottom when messages change
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
            toast({
                title: 'Error',
                description: 'Failed to load datasets',
                variant: 'destructive',
            });
        }
    };

    const createNewConversation = async () => {
        if (!selectedDataset) return;

        try {
            setLoading(true);
            const response = await conversationsAPI.create(selectedDataset);
            setCurrentConversation(response.data);
            setMessages([]);
        } catch (error) {
            console.error('Error creating conversation:', error);
            toast({
                title: 'Error',
                description: 'Failed to create conversation',
                variant: 'destructive',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim() || !currentConversation || sending) return;

        const userQuery = query.trim();
        setQuery('');
        setSending(true);

        // Optimistically add user message
        const tempUserMessage: Message = {
            id: Date.now(),
            role: 'user',
            content: userQuery,
            created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, tempUserMessage]);

        try {
            const response = await conversationsAPI.sendMessage(
                currentConversation.id,
                userQuery
            );

            // Add assistant response
            setMessages((prev) => [...prev, response.data]);
        } catch (error: any) {
            console.error('Error sending message:', error);
            toast({
                title: 'Error',
                description: error.response?.data?.detail || 'Failed to send message',
                variant: 'destructive',
            });
        } finally {
            setSending(false);
        }
    };

    const handleNewChat = () => {
        setCurrentConversation(null);
        setMessages([]);
        setQuery('');
        if (selectedDataset) {
            createNewConversation();
        }
    };

    const selectedDatasetInfo = datasets.find((d) => d.id === selectedDataset);

    return (
        <div className="h-screen flex flex-col bg-muted">
            {/* Header */}
            <div className="bg-card border-b border-border px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate('/analytics')}
                        className="text-muted-foreground hover:text-foreground"
                    >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back
                    </Button>
                    <div>
                        <h1 className="text-xl font-bold text-foreground">Conversational Analytics</h1>
                        {selectedDatasetInfo && (
                            <p className="text-sm text-muted-foreground">{selectedDatasetInfo.name}</p>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {/* Dataset Selector */}
                    <select
                        value={selectedDataset || ''}
                        onChange={(e) => {
                            setSelectedDataset(Number(e.target.value));
                            setCurrentConversation(null);
                            setMessages([]);
                        }}
                        className="px-3 py-2 bg-card border border-border rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    >
                        <option value="">Select dataset...</option>
                        {datasets.map((dataset) => (
                            <option key={dataset.id} value={dataset.id}>
                                {dataset.name}
                            </option>
                        ))}
                    </select>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleNewChat}
                        disabled={!selectedDataset}
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        New Chat
                    </Button>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-6 py-8">
                <div className="max-w-4xl mx-auto">
                    <AnimatePresence>
                        {messages.length === 0 && !loading ? (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-center py-20"
                            >
                                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center mb-6 shadow-lg mx-auto">
                                    <Sparkles className="w-8 h-8 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold mb-2 text-foreground">
                                    Start a conversation
                                </h3>
                                <p className="text-muted-foreground mb-8">
                                    Ask questions about your data in natural language
                                </p>

                                {/* Suggested Queries */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                                    {[
                                        'Show me top 5 products by sales',
                                        'Rank products in tabular format by the sales amount',
                                        'What are the total sales by region?',
                                        'Identify trends in the data',
                                    ].map((suggestion, i) => (
                                        <motion.button
                                            key={i}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={() => setQuery(suggestion)}
                                            className="p-4 text-left bg-card border border-border rounded-xl hover:border-purple-300 hover:shadow-md transition-all"
                                        >
                                            <p className="text-sm text-slate-700">{suggestion}</p>
                                        </motion.button>
                                    ))}
                                </div>
                            </motion.div>
                        ) : (
                            <>
                                {messages.map((message) => (
                                    <ConversationMessageV2
                                        key={message.id}
                                        role={message.role}
                                        content={message.content}
                                        queryData={message.query_data}
                                        processingSteps={message.processing_steps}
                                        timestamp={message.created_at}
                                    />
                                ))}

                                {/* Loading indicator */}
                                {sending && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="flex items-center gap-3 mb-6"
                                    >
                                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center">
                                            <Loader2 className="w-4 h-4 text-white animate-spin" />
                                        </div>
                                        <div className="glass rounded-2xl px-4 py-3">
                                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                <span className="animate-pulse">Thinking...</span>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </>
                        )}
                    </AnimatePresence>
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className="bg-card border-t border-border px-6 py-4">
                <div className="max-w-4xl mx-auto">
                    <form onSubmit={handleSubmit} className="flex gap-3">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder={
                                selectedDataset
                                    ? 'Ask a question about your data...'
                                    : 'Select a dataset first...'
                            }
                            disabled={!selectedDataset || sending}
                            className="flex-1 px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 focus:bg-card transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <Button
                            type="submit"
                            disabled={!query.trim() || !selectedDataset || sending}
                            className="px-6 py-3 bg-gradient-to-br from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-xl shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {sending ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Send className="w-5 h-5" />
                            )}
                        </Button>
                    </form>
                    <p className="text-xs text-slate-400 mt-2 text-center">
                        AI can make mistakes. Verify important information.
                    </p>
                </div>
            </div>
        </div>
    );
}
