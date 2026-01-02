import { useEffect, useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import {
    Send,
    Download,
    Database,
    Pin,
    Edit2,
    Settings2,
    Sparkles,
    Terminal,
    PieChart,
    ChevronRight,
    Search,
    RefreshCw,
    Plus,
    TrendingUp,
    AlertCircle,
    History as HistoryIcon,
    Check
} from 'lucide-react';
import { datasetsAPI, queriesAPI, dashboardsAPI } from '../lib/api';
import { conversationsAPI } from '../lib/conversationsAPI';
import ChartRenderer from '../components/ChartRenderer';
import SQLEditor from '../components/SQLEditor';
import ChartEditor from '../components/ChartEditor';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useToast } from '../hooks/use-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
    role: 'user' | 'assistant' | 'error';
    content: any;
    id?: number;
    isRepairing?: boolean;
}

export default function AnalyticsPage() {
    const { toast } = useToast();
    const location = useLocation();
    const preselectedDatasetId = location.state?.datasetId;

    const [datasets, setDatasets] = useState<any[]>([]);
    const [selectedDataset, setSelectedDataset] = useState<number | null>(preselectedDatasetId || null);
    const [selectedDatasetInfo, setSelectedDatasetInfo] = useState<any>(null);
    const [editingMessageId, setEditingMessageId] = useState<number | null>(null);
    const [tweakingChartId, setTweakingChartId] = useState<number | null>(null);
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [dashboards, setDashboards] = useState<any[]>([]);
    const [pinningMessageId, setPinningMessageId] = useState<number | null>(null);

    // Conversational NLP state
    const [currentConversation, setCurrentConversation] = useState<any>(null);
    const [useConversationalMode, setUseConversationalMode] = useState(true); // Enable by default

    const navigate = useNavigate();

    // Initialize session ID from navigation state (history) or create new
    const [sessionId, setSessionId] = useState<string>(() => {
        return location.state?.sessionId || crypto.randomUUID();
    });

    useEffect(() => {
        // If we navigated here with a session ID, ensure we use it
        if (location.state?.sessionId) {
            setSessionId(location.state.sessionId);
        }
    }, [location.state]);

    useEffect(() => {
        loadDatasets();
    }, []);

    useEffect(() => {
        if (datasets.length > 0) {
            // Prioritize dataset from location state (resume chat)
            const resumeDatasetId = location.state?.datasetId;
            let datasetToSelect = selectedDataset;

            if (resumeDatasetId) {
                const exists = datasets.find(d => d.id === resumeDatasetId);
                if (exists) {
                    datasetToSelect = resumeDatasetId;
                    setSelectedDataset(resumeDatasetId);
                }
            } else if (!selectedDataset) {
                // Default to first if none selected
                datasetToSelect = datasets[0].id;
                setSelectedDataset(datasetToSelect);
            }

            if (datasetToSelect) {
                setSelectedDatasetInfo(datasets.find((d) => d.id === datasetToSelect));
            }
        }
    }, [datasets, location.state]);

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

    const loadDashboards = async () => {
        try {
            const res = await dashboardsAPI.list();
            setDashboards(res.data);
            // Auto-create 'Main Dashboard' if none exist
            if (res.data.length === 0) {
                const newDash = await dashboardsAPI.create({ name: "Main Dashboard" });
                setDashboards([newDash.data]);
            }
        } catch (e) { console.error(e); }
    };

    useEffect(() => { loadDashboards(); }, []);



    // Track previous state to prevent spurious reloads
    const previousState = useRef<{ datasetId: number | null, sessionId: string | null }>({
        datasetId: null,
        sessionId: null
    });

    const loadHistory = async (datasetId: number, currentSessionId: string) => {
        try {
            setLoading(true);
            setMessages([]); // Clear previous messages while loading

            // Fetch history for SPECIFIC session
            const response = await queriesAPI.history(50, datasetId, 'desc', currentSessionId);

            // If we are resuming a session but it has no messages for this dataset,
            // it's effectively a new chat for this view.
            if (response.data.length === 0) {
                setMessages([]);
                return;
            }

            const historyMessages = response.data.flatMap((q: any) => {
                const msgs: Message[] = [];
                // User message
                msgs.push({ role: 'user', content: q.natural_language_query, id: q.id });

                const isError = q.status === 'error';
                const errText = q.error_message ? q.error_message.toLowerCase() : '';
                const isRepairable = isError && (
                    errText.includes('parser error') ||
                    errText.includes('jsonb') ||
                    errText.includes('syntax error') ||
                    errText.includes('forbidden keyword') ||
                    errText.includes('drop table')
                );

                // Assistant message (if we have ANY content OR it is repairable)
                // If repairable, we force it to show as assistant so we can see what code failed and the spinner
                const hasContent = q.generated_sql || (q.result_data && q.result_data.length > 0) || q.python_chart || q.insights;

                if (hasContent || isRepairable) {
                    // Ensure visualization config has data (defensive)
                    let vizConfig = q.visualization_config;
                    if (vizConfig && !vizConfig.data && q.result_data) {
                        vizConfig = { ...vizConfig, data: q.result_data };
                    }

                    msgs.push({
                        role: 'assistant',
                        content: {
                            natural_language_query: q.natural_language_query,
                            generated_sql: q.generated_sql,
                            result_data: q.result_data,
                            visualization_config: vizConfig,
                            python_chart: q.python_chart,
                            insights: q.insights,
                            execution_time: q.execution_time
                        },
                        id: q.id,
                        isRepairing: isRepairable
                    });
                }

                // Error message (ONLY if NOT repairable)
                // If it is repairable, we suppressed it above and merged it into assistant with isRepairing=true
                if (isError && !isRepairable) {
                    msgs.push({ role: 'error', content: q.error_message || "Analysis failed", id: q.id });
                }
                return msgs;
            });

            // Maintain chronological order (Oldest -> Newest) just like live chat
            setMessages(historyMessages);

            // AUTO-REPAIR LOGIC
            // Check for known "repairable" items (now flagged on assistant role) and trigger background retry
            historyMessages.forEach((msg: Message) => {
                if (msg.role === 'assistant' && msg.isRepairing && msg.id) {
                    console.log(`Auto-repairing query ${msg.id}...`);
                    // Trigger background repair
                    queriesAPI.retryQuery(msg.id).then(res => {
                        // Hot-swap the message in state
                        setMessages(prev => prev.map(m => {
                            // Only update if it's the exact message being repaired and it's still marked as repairing
                            if (m.id === msg.id && m.role === 'assistant' && m.isRepairing) {
                                const data = res.data;
                                let vizConfig = data.visualization_config;
                                if (vizConfig && !vizConfig.data && data.result_data) {
                                    vizConfig = { ...vizConfig, data: data.result_data };
                                }
                                return {
                                    role: 'assistant',
                                    content: {
                                        natural_language_query: data.natural_language_query,
                                        generated_sql: data.generated_sql,
                                        result_data: data.result_data,
                                        visualization_config: vizConfig,
                                        python_chart: data.python_chart,
                                        insights: data.insights,
                                        execution_time: data.execution_time
                                    },
                                    id: msg.id,
                                    isRepairing: false // DONE repairing
                                } as Message;
                            }
                            return m;
                        }));
                    }).catch(err => console.error("Auto-repair failed", err));
                }
            });

        } catch (error) {
            console.error('Error loading history:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedDataset && sessionId) {
            // Load history if EITHER dataset OR session changed
            if (previousState.current.datasetId !== selectedDataset || previousState.current.sessionId !== sessionId) {
                previousState.current = { datasetId: selectedDataset, sessionId: sessionId };
                loadHistory(selectedDataset, sessionId);
            }
        }
    }, [selectedDataset, sessionId]);

    // Create conversation when dataset is selected (for conversational mode)
    useEffect(() => {
        if (selectedDataset && useConversationalMode && !currentConversation) {
            createConversation();
        }
    }, [selectedDataset, useConversationalMode]);

    const createConversation = async () => {
        if (!selectedDataset) return;
        try {
            const response = await conversationsAPI.create(selectedDataset);
            setCurrentConversation(response.data);
        } catch (error) {
            console.error('Error creating conversation:', error);
            // Fall back to non-conversational mode if conversation creation fails
            setUseConversationalMode(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim() || !selectedDataset || loading) return;

        const userMessage = { role: 'user', content: query };
        setMessages((prev) => [...prev, userMessage]);
        const userQuery = query;
        setQuery('');
        setLoading(true);

        try {
            // Use conversational API if available, otherwise fall back to regular API
            if (useConversationalMode && currentConversation) {
                const response = await conversationsAPI.sendMessage(
                    currentConversation.id,
                    userQuery
                );

                const messageData = response.data;

                // Convert conversational response to existing message format
                const assistantMessage = {
                    role: 'assistant',
                    content: {
                        natural_language_query: userQuery,
                        generated_sql: messageData.query_data?.generated_sql,
                        result_data: messageData.query_data?.result_data,
                        visualization_config: messageData.query_data?.visualization
                            ? {
                                type: messageData.query_data.visualization.type,
                                xAxis: messageData.query_data.visualization.x_axis,
                                yAxis: messageData.query_data.visualization.y_axis,
                                data: messageData.query_data.result_data,
                                columns: messageData.query_data.columns
                            }
                            : null,
                        insights: messageData.content, // Natural language response
                        execution_time: messageData.query_data?.execution_time_ms || 0,
                        processing_steps: messageData.processing_steps
                    },
                };
                setMessages((prev) => [...prev, assistantMessage]);
            } else {
                // Fall back to original API
                const response = await queriesAPI.ask({
                    dataset_id: selectedDataset,
                    query: userQuery,
                    session_id: sessionId
                });

                const data = response.data;

                if (data.status === 'error') {
                    const errorMessage = {
                        role: 'error',
                        content: data.error_message || "An error occurred while processing your request.",
                    };
                    setMessages((prev) => [...prev, errorMessage]);
                } else {
                    const assistantMessage = {
                        role: 'assistant',
                        content: data,
                    };
                    setMessages((prev) => [...prev, assistantMessage]);
                }
            }

            // Refresh sessions list after first message
            if (messages.length === 0) {
                // loadSessions(selectedDataset); // Removed
            }
        } catch (error: any) {
            const errorMessage = {
                role: 'error',
                content: error.response?.data?.detail || 'Error processing query',
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setLoading(false);
            // Do not reload history here, it brings back old sessions
        }
    };

    const handleRunSQL = async (sql: string, originalMessage: any) => {
        if (!selectedDataset) return;
        setLoading(true);
        try {
            const res = await queriesAPI.execute({
                dataset_id: selectedDataset,
                sql: sql
            });

            const newMessage = {
                role: 'assistant',
                content: {
                    natural_language_query: originalMessage.content.natural_language_query || "Modified Query",
                    generated_sql: sql,
                    result_data: res.data.result_data,
                    visualization_config: res.data.visualization_config,
                    python_chart: res.data.python_chart,
                    insights: "Results updated based on modified SQL.",
                    execution_time: res.data.execution_time
                }
            };

            setMessages((prev) => [...prev, { role: 'user', content: "Re-ran modified SQL" }, newMessage]);
            setEditingMessageId(null);
        } catch (error: any) {
            console.error('Error executing SQL:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRegenerate = async (queryText: string) => {
        if (!queryText.trim() || !selectedDataset) return;
        setLoading(true);

        // Optimistic update for UI feedback (optional, or just loading spinner)
        // We don't add a user message because it's already there in history!
        // We just want to replace the error message with the new result?
        // Actually, easiest is to just behave like a new message for now, OR filter out the error?
        // Let's just append new transaction. It's safer.

        try {
            // Append user message only if we want to trace it, but for regeneration of OLD message...
            // Ideally we replace the old error. But editing history is complex.
            // Let's just append for now.
            setMessages((prev) => [...prev, { role: 'user', content: queryText }]);

            const response = await queriesAPI.ask({
                dataset_id: selectedDataset,
                query: queryText,
                session_id: sessionId
            });

            const data = response.data;
            const assistantMessage = {
                role: 'assistant',
                content: {
                    natural_language_query: data.natural_language_query,
                    generated_sql: data.generated_sql,
                    result_data: data.result_data,
                    visualization_config: data.visualization_config,
                    python_chart: data.python_chart,
                    insights: data.insights,
                    execution_time: data.execution_time
                }
            };
            setMessages((prev) => [...prev, assistantMessage]);
            // loadSessions(selectedDataset); // Refresh list
        } catch (error: any) {
            const errorMessage = {
                role: 'error',
                content: error.response?.data?.detail || "An error occurred while processing your request."
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handlePin = async (message: any, idx: number) => {
        if (!dashboards.length) return;
        setPinningMessageId(idx);

        try {
            // Use first dashboard for now (MVP)
            const targetDashboardId = dashboards[0].id;

            await dashboardsAPI.addWidget(targetDashboardId, {
                title: message.content.natural_language_query || "Pinned Insight",
                type: message.content.python_chart ? 'chart' : 'query',
                data_source: selectedDatasetInfo?.name || "Dataset",
                viz_config: message.content.visualization_config,
                python_chart: message.content.python_chart,
                sql: message.content.generated_sql
            });

            toast({ title: "Pinned to Dashboard", description: "Insight added to your main dashboard." });

            // Visual feedback delay
            setTimeout(() => setPinningMessageId(null), 1000);

        } catch (e) {
            console.error("Pin failed", e);
            toast({ title: "Pin Failed", description: "Could not save insight.", variant: "destructive" });
            setPinningMessageId(null);
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setQuery('');
        setEditingMessageId(null);
        setTweakingChartId(null);

        // Generate NEW session ID
        setSessionId(crypto.randomUUID());

        // Reset conversation for conversational mode
        setCurrentConversation(null);
        if (useConversationalMode && selectedDataset) {
            createConversation();
        }

        // Refresh session list (current session is now "history" if it had messages)
        // Refresh session list (current session is now "history" if it had messages)
        // if (selectedDataset) loadSessions(selectedDataset); // Removed

        toast({
            title: "New Chat Started",
            description: "Previous conversation saved to history."
        });
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500 pb-20">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-foreground">
                        Agent Analysis
                    </h1>
                    <p className="text-muted-foreground mt-1">Chat with your datasets to extract insights and generate reports.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 h-[calc(100vh-220px)]">

                {/* Left Sidebar: Dataset Selection & Context */}
                <div className="lg:col-span-1 flex flex-col gap-6 overflow-hidden h-full pr-1">

                    {/* Dataset Selector */}
                    <Card className="bg-card border-border shadow-sm overflow-hidden shrink-0">
                        <CardHeader className="p-4 border-b border-border bg-muted/30">
                            <CardTitle className="text-xs font-bold uppercase tracking-wider flex items-center gap-2 text-muted-foreground">
                                <Database className="w-4 h-4" /> Environment
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 space-y-4">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                <select
                                    value={selectedDataset || ''}
                                    onChange={(e) => setSelectedDataset(Number(e.target.value))}
                                    className="w-full pl-10 pr-4 py-2 bg-card border border-border rounded-lg text-sm focus:ring-2 focus:ring-slate-900/5 focus:border-slate-900 transition-all appearance-none cursor-pointer text-foreground"
                                >
                                    <option value="">Choose a dataset...</option>
                                    {datasets.map((dataset) => (
                                        <option key={dataset.id} value={dataset.id}>
                                            {dataset.name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {selectedDatasetInfo && (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="p-3 rounded-lg bg-muted border border-border space-y-2"
                                >
                                    <div className="flex justify-between text-[10px]">
                                        <span className="text-muted-foreground font-medium">ROWS</span>
                                        <span className="font-bold text-foreground">{selectedDatasetInfo.row_count?.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between text-[10px]">
                                        <span className="text-muted-foreground font-medium">COLS</span>
                                        <span className="font-bold text-foreground">{selectedDatasetInfo.column_count}</span>
                                    </div>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        className="w-full h-8 text-xs font-medium border-border bg-card hover:bg-muted text-foreground shadow-sm mt-1"
                                        onClick={async () => {
                                            if (!selectedDataset) return;
                                            setLoading(true);
                                            try {
                                                const res = await datasetsAPI.getEDA(selectedDataset);
                                                setMessages(prev => [...prev, {
                                                    role: 'assistant',
                                                    content: {
                                                        natural_language_query: "Performing Auto-EDA...",
                                                        insights: res.data.report,
                                                        python_chart: res.data.visualization,
                                                        execution_time: 0
                                                    }
                                                }]);
                                            } catch (e) {
                                                console.error(e);
                                            } finally {
                                                setLoading(false);
                                            }
                                        }}
                                        disabled={loading}
                                    >
                                        <RefreshCw className={`w-3 h-3 mr-2 ${loading ? 'animate-spin' : ''}`} />
                                        Auto-EDA
                                    </Button>
                                </motion.div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Recent Activity Sidebar (ChatGPT Style) */}
                    {/* Recent Activity Sidebar */}
                    {selectedDataset && (
                        <div className="flex-1 bg-muted p-4 rounded-lg border border-border flex items-center justify-center text-center">
                            <div>
                                <HistoryIcon className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                                <p className="text-xs text-muted-foreground max-w-[150px]">
                                    View past sessions in the <span className="font-medium text-indigo-500 cursor-pointer" onClick={() => navigate('/history')}>History</span> page.
                                </p>
                            </div>
                        </div>
                    )}

                </div>
                {/* Main Interaction Area */}
                <div className="lg:col-span-3 flex flex-col min-h-0">
                    <Card className="flex-1 flex flex-col bg-card border-border shadow-xl overflow-hidden relative">

                        {/* Status Bar */}
                        <div className="px-6 py-3 border-b border-border bg-muted/20 flex items-center justify-between shrink-0">
                            <div className="flex items-center gap-2">
                                <div className={`w-1.5 h-1.5 rounded-full ${loading ? 'bg-primary animate-pulse' : 'bg-slate-300'}`} />
                                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                    {loading ? 'Agent is Processing' : 'Agent Idle'}
                                </span>
                            </div>
                            <div className="flex items-center gap-3">
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={handleNewChat}
                                    className="h-6 px-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground hover:text-foreground hover:bg-slate-100"
                                >
                                    <Plus className="w-3 h-3 mr-1" /> New Chat
                                </Button>
                                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest border-l border-border pl-3">
                                    Instance: Alpha
                                </span>
                            </div>
                        </div>

                        {/* Messages Area */}
                        <CardContent className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar relative bg-muted/20">
                            <AnimatePresence>
                                {messages.length === 0 ? (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="h-full flex flex-col items-center justify-center p-8"
                                    >
                                        <div className="text-center mb-10 max-w-md">
                                            <div className="w-16 h-16 rounded-2xl bg-primary flex items-center justify-center mb-6 shadow-lg mx-auto">
                                                <Sparkles className="w-8 h-8 text-white" />
                                            </div>
                                            <h3 className="text-xl font-bold mb-2 text-foreground">Start a new analysis</h3>
                                            <p className="text-muted-foreground text-sm">
                                                Select a suggested query below or type your own question to explore your data.
                                            </p>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
                                            {[
                                                { icon: Database, text: "Summarize this dataset", query: "Give me a comprehensive summary of this dataset including row counts, column types, and basic statistics." },
                                                { icon: TrendingUp, text: "Identify key trends", query: "Analyze the data to identify the top 3 key trends or patterns over time." },
                                                { icon: PieChart, text: "Visualize distribution", query: "Create a visualization showing the distribution of the main categorical variable." },
                                                { icon: AlertCircle, text: "Find anomalies", query: "Check the dataset for any anomalies or outliers in the numerical columns." }
                                            ].map((suggestion, i) => (
                                                <motion.button
                                                    key={i}
                                                    whileHover={{ scale: 1.02 }}
                                                    whileTap={{ scale: 0.98 }}
                                                    onClick={() => {
                                                        setQuery(suggestion.query);
                                                        // Optional: auto-submit
                                                        // handleSubmit is an event handler, need to adapt or just set query
                                                        // Ideally we want to simulate submission. 
                                                        // I'll just set query for now to let user confirm, OR call a submit helper. 
                                                        // Let's set query and manual submit for better UX control? 
                                                        // User asked "suggested message", usually implies clicking sends it.
                                                        // I'll create a new handler `handleSuggestion(q)` to send immediately.
                                                    }}
                                                    className="flex items-center gap-4 p-4 text-left bg-card border border-border rounded-xl hover:border-slate-400 hover:shadow-md transition-all group"
                                                >
                                                    <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center group-hover:bg-slate-100 transition-colors">
                                                        <suggestion.icon className="w-5 h-5 text-muted-foreground group-hover:text-foreground" />
                                                    </div>
                                                    <div>
                                                        <span className="block text-sm font-bold text-foreground group-hover:text-foreground">{suggestion.text}</span>
                                                        <span className="block text-[10px] text-muted-foreground">Click to ask</span>
                                                    </div>
                                                </motion.button>
                                            ))}
                                        </div>
                                    </motion.div>
                                ) : (
                                    messages.map((message, idx) => (
                                        <motion.div
                                            key={idx}
                                            id={`msg-${idx}`}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'} gap-2`}
                                        >
                                            {/* User Message */}
                                            {message.role === 'user' && (
                                                <div className="bg-primary px-5 py-2.5 rounded-2xl rounded-tr-none text-sm font-medium text-white shadow-md max-w-[85%]">
                                                    {message.content}
                                                </div>
                                            )}

                                            {/* AI Message */}
                                            {message.role === 'assistant' && (
                                                <div className="w-full space-y-4 max-w-[95%]">
                                                    <div className="flex items-center gap-2 text-muted-foreground mb-1 ml-1">
                                                        <Sparkles className="w-4 h-4" />
                                                        <span className="text-[10px] font-bold uppercase tracking-wider">Analysis Result</span>
                                                    </div>

                                                    <div className="bg-card p-6 md:p-8 rounded-2xl rounded-tl-none border border-border shadow-md space-y-6">

                                                        {typeof message.content === 'object' && message.content !== null && message.content.insights && (
                                                            <div className="space-y-3">
                                                                <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                                                                    <Sparkles className="w-3.5 h-3.5 text-foreground" /> Executive Insights
                                                                </div>
                                                                <div className="text-sm prose prose-slate max-w-none text-slate-600 leading-relaxed bg-muted p-6 rounded-xl border border-slate-100">
                                                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                                        {message.content.insights}
                                                                    </ReactMarkdown>
                                                                </div>
                                                            </div>
                                                        )}

                                                        {(typeof message.content === 'object' && message.content !== null && (message.content.visualization_config || message.content.python_chart)) && (
                                                            <div className="space-y-3">
                                                                <div className="flex items-center justify-between">
                                                                    <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                                                                        {(!message.content.python_chart && message.content.visualization_config?.type === 'table') ? (
                                                                            <><Database className="w-3.5 h-3.5 text-foreground" /> Data Result</>
                                                                        ) : (
                                                                            <><PieChart className="w-3.5 h-3.5 text-foreground" /> Visualization</>
                                                                        )}
                                                                    </div>
                                                                    <Button variant="ghost" size="sm" className="h-7 px-2.5 text-[10px] font-bold text-muted-foreground hover:text-foreground"
                                                                        onClick={() => setTweakingChartId(tweakingChartId === idx ? null : idx)}
                                                                    >
                                                                        <Settings2 className="w-3 h-3 mr-1.5" /> Configure
                                                                    </Button>
                                                                </div>
                                                                <div className={`bg-muted/50 p-4 rounded-xl border border-slate-100 min-h-[300px] ${(!message.content.python_chart && message.content.visualization_config?.type === 'table') ? 'overflow-auto block' : 'flex items-center justify-center'}`}>
                                                                    {message.content.python_chart ? (
                                                                        <img src={message.content.python_chart} className="w-full h-auto rounded-lg shadow-sm border border-border" />
                                                                    ) : (
                                                                        (message.content.visualization_config?.data && message.content.visualization_config.data.length > 0) ? (
                                                                            <ChartRenderer config={message.content.visualization_config} />
                                                                        ) : (
                                                                            <div className="text-center text-muted-foreground text-xs py-12">
                                                                                <Database className="w-8 h-8 mx-auto mb-2 opacity-20" />
                                                                                <p>No data rows returned from query.</p>
                                                                            </div>
                                                                        )
                                                                    )}
                                                                </div>
                                                                <div className="mt-4">
                                                                    {typeof message.content === 'object' && message.content !== null && message.content.result_data && message.content.visualization_config && (
                                                                        <div className="border border-border rounded-lg overflow-hidden bg-card">
                                                                            <div className="p-3 border-b border-slate-100 bg-muted flex justify-between items-center">
                                                                                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Analysis Result</span>
                                                                                {message.content.execution_time && (
                                                                                    <span className="text-xs text-muted-foreground">
                                                                                        {message.content.execution_time}ms
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                            <div className="p-4 overflow-x-auto">
                                                                                <ChartRenderer
                                                                                    config={message.content.visualization_config}
                                                                                />
                                                                            </div>
                                                                        </div>
                                                                    )}

                                                                    {message.isRepairing && (
                                                                        <div className="flex items-center gap-2 mt-3 p-3 bg-amber-50 text-amber-700 rounded-lg border border-amber-100 animate-pulse">
                                                                            <RefreshCw className="w-4 h-4 animate-spin" />
                                                                            <span className="text-sm font-medium">Auto-repairing analysis data...</span>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                                {tweakingChartId === idx && (
                                                                    <ChartEditor
                                                                        config={message.content.visualization_config}
                                                                        onSave={(newConf) => {
                                                                            const newMsgs = [...messages];
                                                                            newMsgs[idx].content.visualization_config = newConf;
                                                                            setMessages(newMsgs);
                                                                            setTweakingChartId(null);
                                                                        }}
                                                                        onCancel={() => setTweakingChartId(null)}
                                                                    />
                                                                )}
                                                            </div>
                                                        )}

                                                        {message.content.generated_sql && (
                                                            <div className="border-t border-slate-100 pt-4">
                                                                <details className="group/code space-y-2" open={message.isRepairing}>
                                                                    <summary className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground hover:text-muted-foreground uppercase tracking-widest cursor-pointer select-none transition-colors justify-end">
                                                                        <Terminal className="w-3 h-3" />
                                                                        <span>Analysis Procedure</span>
                                                                        <ChevronRight className="w-3 h-3 group-open/code:rotate-90 transition-transform" />
                                                                    </summary>

                                                                    <div className="pt-2 animate-in fade-in slide-in-from-top-1 duration-200">
                                                                        {editingMessageId === idx ? (
                                                                            <div className="relative">
                                                                                <SQLEditor
                                                                                    initialValue={message.content.generated_sql}
                                                                                    onRun={(newSql) => {
                                                                                        handleRunSQL(newSql, message);
                                                                                        setEditingMessageId(null);
                                                                                    }}
                                                                                />
                                                                                <Button
                                                                                    variant="ghost"
                                                                                    size="sm"
                                                                                    className="absolute top-2 right-2 text-xs text-muted-foreground hover:text-foreground"
                                                                                    onClick={() => setEditingMessageId(null)}
                                                                                >
                                                                                    Cancel
                                                                                </Button>
                                                                            </div>
                                                                        ) : (
                                                                            <div className="bg-muted rounded-lg p-4 font-mono text-xs overflow-x-auto relative group">
                                                                                <pre className="text-muted-foreground">
                                                                                    <code>{message.content.generated_sql}</code>
                                                                                </pre>
                                                                                <Button variant="ghost" size="sm" className="absolute top-2 right-2 h-6 px-2 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity bg-card/50 backdrop-blur-sm"
                                                                                    onClick={() => {
                                                                                        setEditingMessageId(editingMessageId === idx ? null : idx);
                                                                                    }}
                                                                                >
                                                                                    <Edit2 className="w-3 h-3 mr-1.5" /> Edit
                                                                                </Button>
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </details>
                                                            </div>
                                                        )}

                                                        <div className="pt-4 border-t border-slate-100 flex items-center justify-between flex-wrap gap-4 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                                            <div className="flex gap-4">
                                                                <span>Time: {message.content.execution_time}ms</span>
                                                                <span>Engine: Standard-AI</span>
                                                            </div>
                                                            <div className="flex gap-3">
                                                                <button className="hover:text-foreground flex items-center gap-1"><Download className="w-3 h-3" /> Export</button>
                                                                <button
                                                                    className={`hover:text-foreground flex items-center gap-1 ${pinningMessageId === idx ? 'text-emerald-600 font-bold' : ''}`}
                                                                    onClick={() => handlePin(message, idx)}
                                                                    disabled={pinningMessageId === idx}
                                                                >
                                                                    {pinningMessageId === idx ? <Check className="w-3 h-3" /> : <Pin className="w-3 h-3" />}
                                                                    {pinningMessageId === idx ? 'Saved' : 'Save'}
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Error Message */}
                                            {message.role === 'error' && (
                                                <div className="flex flex-col items-start gap-2 max-w-[85%]">
                                                    <div className="bg-red-50 text-red-600 text-xs px-4 py-3 rounded-lg border border-red-100 font-medium">
                                                        {message.content.includes("Parser Error") || message.content.includes("syntax error") ? (
                                                            <div className="flex items-center gap-2">
                                                                <RefreshCw className="w-3 h-3 animate-spin" />
                                                                <span>Recovering analysis data...</span>
                                                            </div>
                                                        ) : (
                                                            message.content
                                                        )}
                                                    </div>
                                                    <Button
                                                        size="sm"
                                                        className="h-8 text-xs bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
                                                        onClick={() => {
                                                            const prevMsg = messages[idx - 1];
                                                            if (prevMsg && prevMsg.role === 'user') {
                                                                handleRegenerate(prevMsg.content);
                                                            }
                                                        }}
                                                    >
                                                        <Sparkles className="w-3 h-3 mr-1.5" /> Generate Results
                                                    </Button>
                                                </div>
                                            )}
                                        </motion.div>
                                    ))
                                )}
                            </AnimatePresence>

                            {loading && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="flex items-center gap-3 text-foreground p-4"
                                >
                                    <div className="flex gap-1 items-center justify-center">
                                        {[0, 1, 2].map((i) => (
                                            <motion.div
                                                key={i}
                                                animate={{ scale: [1, 1.2, 1], opacity: [0.4, 1, 0.4] }}
                                                transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
                                                className="w-1.5 h-1.5 rounded-full bg-primary"
                                            />
                                        ))}
                                    </div>
                                    <span className="text-[10px] font-bold uppercase tracking-widest">Processing...</span>
                                </motion.div>
                            )}
                        </CardContent>

                        {/* Input Area */}
                        <div className="p-6 bg-card border-t border-slate-100 shrink-0">
                            <form onSubmit={handleSubmit} className="relative">
                                <div className="relative flex items-center gap-3 bg-muted border border-border rounded-xl p-1.5 pl-6 focus-within:border-slate-400 focus-within:bg-card transition-all shadow-sm">
                                    <Input
                                        value={query}
                                        onChange={(e) => setQuery(e.target.value)}
                                        placeholder={selectedDataset ? "Ask a question about your data..." : "Select a dataset to begin..."}
                                        className="bg-transparent border-none focus-visible:ring-0 shadow-none text-sm h-11 flex-1 placeholder:text-muted-foreground text-foreground"
                                        disabled={!selectedDataset || loading}
                                    />
                                    <Button
                                        type="submit"
                                        disabled={!selectedDataset || loading || !query.trim()}
                                        className="h-10 px-5 rounded-lg bg-primary text-white hover:bg-black transition-all font-medium text-xs shadow-sm"
                                    >
                                        <Send className="w-3.5 h-3.5 mr-2" />
                                        Send
                                    </Button>
                                </div>
                            </form>
                            <div className="mt-3 px-1 flex items-center justify-between text-[10px] font-medium text-muted-foreground uppercase tracking-widest">
                                <span>Agent V1.0</span>
                                <span>Press Enter to Submit</span>
                            </div>
                        </div>

                    </Card>
                </div>

            </div>
        </div>
    );
}
