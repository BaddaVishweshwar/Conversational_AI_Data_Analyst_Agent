import { useEffect, useState } from 'react';
import { datasetsAPI } from '../lib/api';
import { Database, Upload, Plus, Search, Calendar, Table2, CheckCircle2, Circle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useNavigate } from 'react-router-dom';

export default function DatasetPage() {
    const [datasets, setDatasets] = useState<any[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [selectedDatasets, setSelectedDatasets] = useState<number[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        loadDatasets();
    }, []);

    const loadDatasets = async () => {
        try {
            setLoading(true);
            const response = await datasetsAPI.list();
            setDatasets(response.data);
        } catch (error) {
            console.error('Error loading datasets:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteDataset = async (datasetId: number) => {
        if (confirm('Are you sure you want to delete this dataset?')) {
            try {
                await datasetsAPI.delete(datasetId);
                await loadDatasets();
                // Remove from selected if it was selected
                setSelectedDatasets(prev => prev.filter(id => id !== datasetId));
                alert('Dataset deleted successfully');
            } catch (error: any) {
                console.error('Error deleting dataset:', error);
                alert(error.response?.data?.detail || 'Failed to delete dataset');
            }
        }
    };

    const toggleDatasetSelection = (datasetId: number) => {
        setSelectedDatasets(prev =>
            prev.includes(datasetId)
                ? prev.filter(id => id !== datasetId)
                : [...prev, datasetId]
        );
    };

    const handleStartAnalyzing = () => {
        if (selectedDatasets.length === 0) {
            alert('Please select at least one dataset');
            return;
        }

        // Get current active datasets
        const saved = localStorage.getItem('activeDatasets');
        const currentActive: number[] = saved ? JSON.parse(saved) : [];

        // Merge with selected datasets (avoid duplicates)
        const merged = [...new Set([...currentActive, ...selectedDatasets])];

        // Save to localStorage
        localStorage.setItem('activeDatasets', JSON.stringify(merged));

        // Trigger custom event to notify MainLayout
        window.dispatchEvent(new Event('activeDatasets-changed'));

        // Navigate to analytics with the first selected dataset
        navigate(`/analytics?dataset=${selectedDatasets[0]}`);
    };

    const filteredDatasets = datasets.filter(dataset =>
        dataset.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="h-full overflow-y-auto bg-background">
            <div className="max-w-7xl mx-auto px-6 py-12">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-semibold text-foreground mb-3">
                        Choose a Dataset
                    </h1>
                    <p className="text-muted-foreground text-base">
                        Select from previously uploaded files or connected sources to explore in our AI-enabled platform
                    </p>
                </div>

                {/* Search */}
                <div className="relative max-w-md mx-auto mb-12">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <Input
                        type="text"
                        placeholder="Search datasets..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-12 h-12 bg-muted/50 border-border rounded-xl text-base"
                    />
                </div>

                {/* Datasets Grid */}
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent"></div>
                    </div>
                ) : filteredDatasets.length === 0 ? (
                    <div className="text-center py-20">
                        <Database className="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
                        <p className="text-muted-foreground">
                            {searchQuery ? 'No datasets found matching your search' : 'No datasets uploaded yet'}
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
                        {filteredDatasets.map((dataset) => {
                            const isSelected = selectedDatasets.includes(dataset.id);
                            return (
                                <div
                                    key={dataset.id}
                                    className={`group relative border rounded-xl p-6 hover:bg-muted/30 transition-all bg-card cursor-pointer ${isSelected ? 'border-accent bg-accent/5' : 'border-border'
                                        }`}
                                    onClick={() => toggleDatasetSelection(dataset.id)}
                                >
                                    {/* Selection Checkbox */}
                                    <div className="absolute top-4 left-4">
                                        {isSelected ? (
                                            <CheckCircle2 className="w-5 h-5 text-accent" />
                                        ) : (
                                            <Circle className="w-5 h-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                        )}
                                    </div>

                                    {/* Dataset Icon */}
                                    <div className="flex items-start gap-4 mb-4 ml-8">
                                        <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
                                            <Database className="w-6 h-6 text-accent" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h3 className="text-lg font-semibold text-foreground mb-1 truncate">
                                                {dataset.name}
                                            </h3>
                                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                                <span className="flex items-center gap-1">
                                                    <Table2 className="w-3 h-3" />
                                                    {dataset.row_count?.toLocaleString() || 0} rows
                                                </span>
                                                <span>•</span>
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="w-3 h-3" />
                                                    {new Date(dataset.created_at).toLocaleDateString()}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex items-center gap-2 ml-8">
                                        <Button
                                            variant="default"
                                            size="sm"
                                            className="flex-1 bg-accent hover:bg-accent/90"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                navigate(`/data-view?dataset=${dataset.id}`);
                                            }}
                                        >
                                            Load
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="flex-1 border-border"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                navigate(`/analytics?dataset=${dataset.id}`);
                                            }}
                                        >
                                            Analyze
                                        </Button>
                                    </div>

                                    {/* Delete button on hover */}
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteDataset(dataset.id);
                                        }}
                                        className="absolute top-4 right-4 w-8 h-8 rounded-lg bg-muted border border-border opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-destructive hover:text-white hover:border-destructive z-10"
                                        title="Delete dataset"
                                    >
                                        <span className="text-lg font-bold">×</span>
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Floating Start Analyzing Button */}
                {selectedDatasets.length > 0 && (
                    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50">
                        <Button
                            size="lg"
                            className="bg-accent hover:bg-accent/90 px-8 h-14 text-base shadow-2xl"
                            onClick={handleStartAnalyzing}
                        >
                            Start Analyzing ({selectedDatasets.length} dataset{selectedDatasets.length > 1 ? 's' : ''})
                        </Button>
                    </div>
                )}

                {/* Upload Section */}
                <div className="border-t border-border pt-12">
                    <div className="flex flex-col items-center gap-4">
                        <Button
                            size="lg"
                            className="bg-accent hover:bg-accent/90 px-8 h-12 text-base"
                            onClick={() => {
                                // Trigger file upload
                                const input = document.createElement('input');
                                input.type = 'file';
                                input.accept = '.csv,.xlsx,.xls';
                                input.onchange = async (e: any) => {
                                    const file = e.target.files[0];
                                    if (file) {
                                        try {
                                            setLoading(true);
                                            const response = await datasetsAPI.upload(file);
                                            await loadDatasets();
                                            // Auto-navigate to analytics page with the new dataset
                                            const newDatasetId = response.data.id;
                                            navigate(`/analytics?dataset=${newDatasetId}`);
                                        } catch (error: any) {
                                            console.error('Upload error:', error);
                                            alert(error.response?.data?.detail || 'Failed to upload dataset');
                                            setLoading(false);
                                        }
                                    }
                                };
                                input.click();
                            }}
                        >
                            <Upload className="w-5 h-5 mr-2" />
                            Upload Dataset
                        </Button>

                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <button className="hover:text-accent transition-colors flex items-center gap-1.5">
                                <Plus className="w-4 h-4" />
                                Connect Database
                            </button>
                            <span>•</span>
                            <button className="hover:text-accent transition-colors flex items-center gap-1.5">
                                <Plus className="w-4 h-4" />
                                Connect Cloud Storage
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div >
    );
}
