import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import {
    History as HistoryIcon,
    Search,
    MessageSquare,
    Database,
    Calendar,
    ArrowRight,
    Loader2,
    Trash2
} from 'lucide-react';
import { queriesAPI, datasetsAPI } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { formatDistanceToNow } from 'date-fns';
import { motion } from 'framer-motion';

export default function HistoryPage() {
    const navigate = useNavigate();
    const [history, setHistory] = useState<any[]>([]);
    const [datasets, setDatasets] = useState<Record<number, string>>({});
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [sessionsRes, datasetsRes] = await Promise.all([
                // Fetch unique sessions instead of raw queries
                queriesAPI.getSessions(),
                datasetsAPI.list()
            ]);

            // Create a map of dataset IDs to names for quick lookup
            const datasetMap: Record<number, string> = {};
            datasetsRes.data.forEach((d: any) => {
                datasetMap[d.id] = d.name;
            });
            setDatasets(datasetMap);
            setHistory(sessionsRes.data);
        } catch (error) {
            console.error('Error loading history:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleContinue = (datasetId: number, sessionId: string) => {
        navigate('/analytics', { state: { datasetId, sessionId } });
    };

    const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        console.log("Attempting to delete session:", sessionId);

        if (!confirm('Are you sure you want to delete this chat session?')) return;

        try {
            console.log("Sending delete request...");
            await queriesAPI.deleteSession(sessionId);
            console.log("Delete request successful. Updating state.");
            setHistory(prev => prev.filter(item => item.session_id !== sessionId));
            // Force refresh to be sure
            // loadData(); 
        } catch (error: any) {
            console.error('Error deleting session:', error);
            alert(`Failed to delete session: ${error.response?.data?.detail || error.message}`);
        }
    };

    const filteredHistory = history.filter(item =>
        item.first_query.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.dataset_id && datasets[item.dataset_id]?.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <div className="space-y-6 animate-in fade-in duration-500 pb-20">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-foreground">
                        Chat History
                    </h1>
                    <p className="text-muted-foreground mt-1">Resume your past analysis sessions.</p>
                </div>
                <div className="relative w-full md:w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                        placeholder="Search sessions..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 bg-card"
                    />
                </div>
            </div>

            {/* History List */}
            <Card className="bg-card border-border shadow-sm">
                <CardHeader className="border-b border-slate-50 bg-muted/30">
                    <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center gap-2 text-muted-foreground">
                        <HistoryIcon className="w-4 h-4" /> Past Sessions
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                    {loading ? (
                        <div className="flex items-center justify-center p-12 text-slate-400">
                            <Loader2 className="w-8 h-8 animate-spin" />
                        </div>
                    ) : filteredHistory.length === 0 ? (
                        <div className="flex flex-col items-center justify-center p-12 text-slate-400">
                            <HistoryIcon className="w-12 h-12 mb-4 opacity-20" />
                            <p>No history found</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-slate-100">
                            {filteredHistory.map((item, idx) => (
                                <motion.div
                                    key={item.session_id || idx}
                                    initial={{ opacity: 0, y: 5 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                    className="p-4 hover:bg-muted transition-colors group flex items-start justify-between gap-4 cursor-pointer"
                                    onClick={() => item.dataset_id && handleContinue(item.dataset_id, item.session_id)}
                                >
                                    <div className="flex gap-4">
                                        <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
                                            <MessageSquare className="w-5 h-5 text-indigo-500" />
                                        </div>
                                        <div>
                                            <p className="font-medium text-foreground line-clamp-1">{item.first_query}</p>
                                            <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                                                {item.dataset_id && (
                                                    <span className="flex items-center gap-1 bg-slate-100 px-2 py-0.5 rounded-full">
                                                        <Database className="w-3 h-3" />
                                                        {datasets[item.dataset_id] || `Dataset #${item.dataset_id}`}
                                                    </span>
                                                )}
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="w-3 h-3" />
                                                    {(() => {
                                                        // Fix UTC parsing by ensuring 'Z' is present if missing
                                                        let dateStr = item.created_at;
                                                        if (dateStr && !dateStr.endsWith('Z')) {
                                                            dateStr += 'Z';
                                                        }
                                                        return dateStr ? formatDistanceToNow(new Date(dateStr), { addSuffix: true }) : 'Recently';
                                                    })()}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                            onClick={(e) => handleDelete(e, item.session_id)}
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                                        >
                                            Resume <ArrowRight className="w-4 h-4 ml-1" />
                                        </Button>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
