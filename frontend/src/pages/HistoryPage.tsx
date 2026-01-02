import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Search, Plus, Filter, BarChart3, TrendingUp, AlertCircle,
    Database, Calendar, RefreshCw, X, Upload, ChevronRight,
    LineChart, PieChart
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

interface AnalysisHistory {
    id: string;
    dataset: string;
    insightType: string;
    question: string;
    visualizationType: string;
    sqlGenerated: string;
    date: string;
    status: string;
}

export default function HistoryPage() {
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedDataset, setSelectedDataset] = useState('all');
    const [selectedDate, setSelectedDate] = useState('all');
    const [showFilters, setShowFilters] = useState(false);
    const [history, setHistory] = useState<AnalysisHistory[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            setLoading(true);
            // TODO: Replace with actual API call
            // Simulated data for now
            const mockHistory: AnalysisHistory[] = [
                {
                    id: '1',
                    dataset: 'Sales_Q4_india.csv',
                    insightType: 'Top Analysis',
                    question: 'Which region drove the highest revenue growth',
                    visualizationType: 'Line & Bar',
                    sqlGenerated: '95%',
                    date: '2 days ago',
                    status: 'Last opened up!'
                },
                {
                    id: '2',
                    dataset: 'Retail_Forecast.csv',
                    insightType: 'Forecast',
                    question: 'Predict sales for the next 6 months',
                    visualizationType: 'Forecast Line',
                    sqlGenerated: '92%',
                    date: '1 week ago',
                    status: "You're all caught up!"
                },
                {
                    id: '3',
                    dataset: 'Products_2023.csv',
                    insightType: 'Top Sellers',
                    question: 'Show me the top-selling products in Q4',
                    visualizationType: 'Bar',
                    sqlGenerated: '98%',
                    date: 'Apr 3, 2024',
                    status: "You're all caught up!"
                }
            ];
            setHistory(mockHistory);
        } catch (error) {
            console.error('Error loading history:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (itemId: string, e: React.MouseEvent) => {
        e.stopPropagation();

        if (!confirm('Are you sure you want to delete this analysis? This cannot be undone.')) {
            return;
        }

        try {
            // TODO: Replace with actual API call to delete
            // await api.delete(`/conversations/${itemId}`);

            // Remove from local state
            setHistory(prev => prev.filter(item => item.id !== itemId));
        } catch (error) {
            console.error('Error deleting history:', error);
            alert('Failed to delete analysis. Please try again.');
        }
    };

    const filteredHistory = history.filter(item => {
        const matchesSearch = item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
            item.dataset.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesDataset = selectedDataset === 'all' || item.dataset === selectedDataset;
        return matchesSearch && matchesDataset;
    });

    const getVisualizationIcon = (type: string) => {
        switch (type.toLowerCase()) {
            case 'line & bar':
            case 'line':
                return <LineChart className="w-3 h-3" />;
            case 'bar':
                return <BarChart3 className="w-3 h-3" />;
            case 'pie':
                return <PieChart className="w-3 h-3" />;
            default:
                return <BarChart3 className="w-3 h-3" />;
        }
    };

    const getInsightIcon = (type: string) => {
        switch (type.toLowerCase()) {
            case 'forecast':
                return <TrendingUp className="w-4 h-4" />;
            case 'anomaly detection':
                return <AlertCircle className="w-4 h-4" />;
            default:
                return <BarChart3 className="w-4 h-4" />;
        }
    };

    return (
        <div className="h-full overflow-y-auto bg-background">
            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Header */}
                <div className="flex items-start justify-between mb-8">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                                <BarChart3 className="w-5 h-5 text-accent" />
                            </div>
                            <h1 className="text-3xl font-semibold text-foreground">
                                Analysis History
                            </h1>
                        </div>
                        <p className="text-muted-foreground text-sm ml-13">
                            Your past data explorations, insights, and decisions — organized.
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Search */}
                        <div className="relative w-80">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <Input
                                type="text"
                                placeholder="Search dataset, metric, or question..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10 bg-muted/50 border-border"
                            />
                        </div>

                        {/* New Analysis Button */}
                        <Button
                            className="bg-accent hover:bg-accent/90 gap-2"
                            onClick={() => navigate('/chat')}
                        >
                            <Plus className="w-4 h-4" />
                            New Analysis
                        </Button>
                    </div>
                </div>

                {/* Filters Bar */}
                <div className="flex items-center gap-3 mb-6">
                    {/* Dataset Filter */}
                    <select
                        value={selectedDataset}
                        onChange={(e) => setSelectedDataset(e.target.value)}
                        className="px-4 py-2 bg-muted/50 border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                        <option value="all">All Datasets</option>
                        <option value="Sales_Q4_india.csv">Sales_Q4_india.csv</option>
                        <option value="Retail_Forecast.csv">Retail_Forecast.csv</option>
                        <option value="Products_2023.csv">Products_2023.csv</option>
                    </select>

                    {/* Date Filter */}
                    <select
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        className="px-4 py-2 bg-muted/50 border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                    >
                        <option value="all">All Dates</option>
                        <option value="today">Today</option>
                        <option value="week">This Week</option>
                        <option value="month">This Month</option>
                    </select>

                    {/* Filter Toggle */}
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowFilters(!showFilters)}
                        className="gap-2"
                    >
                        <Filter className="w-4 h-4" />
                        Filter
                    </Button>

                    <div className="flex-1" />

                    {/* Action Buttons */}
                    <Button variant="ghost" size="sm" onClick={loadHistory}>
                        <RefreshCw className="w-4 h-4" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                            setSearchQuery('');
                            setSelectedDataset('all');
                            setSelectedDate('all');
                        }}
                    >
                        <X className="w-4 h-4" />
                    </Button>
                </div>

                {/* History Grid */}
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent"></div>
                    </div>
                ) : filteredHistory.length === 0 ? (
                    /* Empty State */
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                        <div className="w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center mb-6">
                            <BarChart3 className="w-10 h-10 text-accent" />
                        </div>
                        <h2 className="text-2xl font-semibold text-foreground mb-3">
                            No Analysis Yet
                        </h2>
                        <p className="text-muted-foreground mb-2 max-w-md">
                            Start by uploading a dataset and asking questions like:
                        </p>
                        <ul className="text-muted-foreground text-sm mb-6 space-y-1">
                            <li>"What are the top revenue drivers?"</li>
                            <li>"Show sales trends by region"</li>
                            <li>"Detect anomalies in this dataset?"</li>
                        </ul>
                        <Button
                            className="bg-accent hover:bg-accent/90 gap-2"
                            onClick={() => navigate('/datasets')}
                        >
                            <Upload className="w-4 h-4" />
                            Upload Dataset
                        </Button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {filteredHistory.map((item) => (
                            <div
                                key={item.id}
                                className="group relative border border-border rounded-xl p-5 hover:bg-muted/30 transition-all bg-card cursor-pointer"
                                onClick={() => navigate(`/chat?session=${item.id}`)}
                            >
                                {/* Header */}
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                        <Database className="w-3 h-3" />
                                        <span className="font-medium">Dataset:</span>
                                        <span className="text-foreground truncate max-w-[180px]">
                                            {item.dataset}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <button
                                            onClick={(e) => handleDelete(item.id, e)}
                                            className="p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors opacity-0 group-hover:opacity-100"
                                            title="Delete this analysis"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                        <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                </div>

                                {/* Insight Type */}
                                <div className="flex items-center gap-2 mb-3">
                                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                        {getInsightIcon(item.insightType)}
                                        <span>Insight Type:</span>
                                        <span className="text-foreground font-medium">{item.insightType}</span>
                                    </div>
                                </div>

                                {/* Question */}
                                <p className="text-sm text-foreground mb-4 line-clamp-2">
                                    {item.question}
                                </p>

                                {/* Metadata Row */}
                                <div className="flex items-center justify-between">
                                    {/* Visualization Type */}
                                    <div className="flex items-center gap-2">
                                        <div className="flex items-center gap-1 px-2 py-1 bg-muted/50 rounded text-xs">
                                            {getVisualizationIcon(item.visualizationType)}
                                            <span className="text-muted-foreground">{item.visualizationType}</span>
                                        </div>
                                        <div className="flex items-center gap-1 px-2 py-1 bg-accent/10 rounded text-xs">
                                            <span className="text-accent">SQL Generated</span>
                                            <span className="text-accent font-semibold">{item.sqlGenerated}</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Resume Analysis Button */}
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="w-full mt-4 border-accent/20 text-accent hover:bg-accent/10 gap-2"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        navigate(`/chat?session=${item.id}`);
                                    }}
                                >
                                    Resume Analysis
                                    <ChevronRight className="w-3 h-3" />
                                </Button>

                                {/* Footer */}
                                <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
                                    <span className="text-xs text-muted-foreground">{item.date}</span>
                                    <span className="text-xs text-muted-foreground italic">{item.status}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
