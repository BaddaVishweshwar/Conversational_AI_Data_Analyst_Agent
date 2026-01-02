import { useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { datasetsAPI, connectionsAPI } from '../lib/api';
import {
    Upload,
    Trash2,
    FileSpreadsheet,
    BarChart,
    Clock,
    FileText,
    Plus,
    CheckCircle2,
    XCircle,
    Loader2,
    Search,
    Database
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

export default function DatasetPage() {
    const [datasets, setDatasets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [dbConnections, setDbConnections] = useState<any[]>([]);
    const [selectedConnId, setSelectedConnId] = useState('');
    const [dbDatasetName, setDbDatasetName] = useState('');

    const [dbTables, setDbTables] = useState<string[]>([]);
    const [selectedTable, setSelectedTable] = useState('');
    const [loadingTables, setLoadingTables] = useState(false);

    useEffect(() => {
        loadDatasets();
        loadConnections();
    }, []);

    useEffect(() => {
        if (selectedConnId) {
            loadTables(parseInt(selectedConnId));
        } else {
            setDbTables([]);
            setSelectedTable('');
        }
    }, [selectedConnId]);

    const loadConnections = async () => {
        try {
            const res = await connectionsAPI.list();
            setDbConnections(res.data);
        } catch (e) { console.error(e); }
    };

    const loadTables = async (connId: number) => {
        setLoadingTables(true);
        try {
            const res = await connectionsAPI.getTables(connId);
            setDbTables(res.data);
            if (res.data.length > 0) setSelectedTable(res.data[0]);
        } catch (e) {
            console.error('Error loading tables', e);
            setDbTables([]);
        } finally {
            setLoadingTables(false);
        }
    };

    const handleDbConnect = async () => {
        if (!selectedConnId || !selectedTable) {
            alert("Please select a connection and a table");
            return;
        }
        setUploading(true);
        try {
            await datasetsAPI.createFromConnection({
                name: dbDatasetName || `${selectedTable} (DB)`,
                connection_id: parseInt(selectedConnId),
                table_name: selectedTable
            });
            await loadDatasets();
            setDbDatasetName('');
            setSelectedConnId('');
            setSelectedTable('');
            setDbTables([]);
        } catch (e: any) {
            alert(e.response?.data?.detail || 'Error linking database');
        } finally {
            setUploading(false);
        }
    };

    const loadDatasets = async () => {
        try {
            const response = await datasetsAPI.list();
            if (Array.isArray(response.data)) {
                setDatasets(response.data);
            }
        } catch (error) {
            console.error('Error loading datasets:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const hasProcessing = datasets.some(d => d.status === 'processing');
        if (!hasProcessing) return;
        const interval = setInterval(() => { loadDatasets(); }, 3000);
        return () => clearInterval(interval);
    }, [datasets]);

    const onDrop = async (acceptedFiles: File[]) => {
        if (acceptedFiles.length === 0) return;
        const file = acceptedFiles[0];
        setUploading(true);
        try {
            await datasetsAPI.upload(file);
            await loadDatasets();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Error uploading file');
        } finally {
            setUploading(false);
        }
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-excel': ['.xls'],
        },
        maxFiles: 1,
    });

    const handleDelete = async (id: number) => {
        if (!confirm('Permanently delete this dataset? All associated insights will be lost.')) return;
        try {
            await datasetsAPI.delete(id);
            await loadDatasets();
        } catch (error: any) {
            console.error('Delete error:', error);
        }
    };

    const filteredDatasets = datasets.filter(d =>
        d.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-10 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-bold font-display tracking-tight text-slate-900">
                        Data Source Manager
                    </h1>
                    <p className="text-slate-500 mt-2">
                        Import and manage the raw datasets feeding your AI engine.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Left: Upload Zone */}
                <div className="lg:col-span-1">
                    <Card className="bg-white border border-slate-200 shadow-xl overflow-hidden sticky top-8">
                        <CardHeader className="p-6 border-b border-slate-100 bg-slate-50/50">
                            <CardTitle className="text-sm font-bold uppercase tracking-widest flex items-center gap-2 text-slate-900">
                                <Plus className="w-4 h-4 text-slate-900" /> Import Source
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-6">
                            <div
                                {...getRootProps()}
                                className={`relative group border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${isDragActive
                                    ? 'border-slate-900 bg-slate-50'
                                    : 'border-slate-200 hover:border-slate-400 hover:bg-slate-50'
                                    }`}
                            >
                                <input {...getInputProps()} />
                                <div className={`w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center transition-transform duration-300 group-hover:scale-110 ${uploading ? 'bg-primary/20' : 'bg-slate-100'}`}>
                                    {uploading ? (
                                        <Loader2 className="w-8 h-8 text-slate-900 animate-spin" />
                                    ) : (
                                        <Upload className={`w-8 h-8 ${isDragActive ? 'text-slate-900' : 'text-slate-400 group-hover:text-slate-600'}`} />
                                    )}
                                </div>

                                <div className="space-y-1">
                                    <p className="text-sm font-bold tracking-tight text-slate-900">
                                        {uploading ? 'Uploading...' : isDragActive ? 'Release to Start' : 'Drag & Drop CSV/Excel'}
                                    </p>
                                    <p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">
                                        Max size: 100MB
                                    </p>
                                </div>

                                {isDragActive && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="absolute inset-0 bg-slate-900/5 backdrop-blur-sm rounded-2xl flex items-center justify-center pointer-events-none"
                                    >
                                        <div className="bg-slate-900 text-white p-3 rounded-full shadow-2xl">
                                            <CheckCircle2 className="w-6 h-6" />
                                        </div>
                                    </motion.div>
                                )}
                            </div>

                            <div className="mt-6 space-y-4">
                                <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                    <Clock className="w-3 h-3" /> System Capability
                                </h4>
                                <div className="space-y-2">
                                    {['CSV Processing', 'Excel Multi-sheet', 'Automatic Profiling'].map((feature, i) => (
                                        <div key={i} className="flex items-center gap-2 text-xs font-medium text-slate-600">
                                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> {feature}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Database Connection Card */}
                    <Card className="bg-white border border-slate-200 shadow-xl overflow-hidden mt-6">
                        <CardHeader className="p-6 border-b border-slate-100 bg-slate-50/50">
                            <CardTitle className="text-sm font-bold uppercase tracking-widest flex items-center gap-2 text-slate-900">
                                <Database className="w-4 h-4 text-slate-900" /> Connect Database
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-6 space-y-4">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-500 uppercase">Select Source</label>
                                <select
                                    className="w-full text-sm p-2 rounded-md border border-slate-200"
                                    value={selectedConnId}
                                    onChange={e => setSelectedConnId(e.target.value)}
                                >
                                    <option value="">-- Choose Connection --</option>
                                    {dbConnections.map(c => (
                                        <option key={c.id} value={c.id}>{c.name} ({c.type})</option>
                                    ))}
                                </select>
                                {dbConnections.length === 0 && (
                                    <p className="text-xs text-slate-400">
                                        No connections found. <Link to="/connections" className="text-primary hover:underline">Manage Connections</Link>
                                    </p>
                                )}
                            </div>

                            {selectedConnId && (
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-500 uppercase">Select Table</label>
                                    {loadingTables ? (
                                        <div className="flex items-center gap-2 text-xs text-slate-500">
                                            <Loader2 className="w-3 h-3 animate-spin" /> Fetching tables...
                                        </div>
                                    ) : (
                                        <select
                                            className="w-full text-sm p-2 rounded-md border border-slate-200"
                                            value={selectedTable}
                                            onChange={e => setSelectedTable(e.target.value)}
                                        >
                                            <option value="">-- Choose Table --</option>
                                            {dbTables.map(t => (
                                                <option key={t} value={t}>{t}</option>
                                            ))}
                                        </select>
                                    )}
                                </div>
                            )}

                            {selectedConnId && (
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-500 uppercase">Dataset Name</label>
                                    <input
                                        className="w-full text-sm p-2 rounded-md border border-slate-200"
                                        placeholder="e.g. Sales DB"
                                        value={dbDatasetName}
                                        onChange={e => setDbDatasetName(e.target.value)}
                                    />
                                    <Button
                                        className="w-full mt-2"
                                        onClick={handleDbConnect}
                                        disabled={uploading}
                                    >
                                        {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Link Database'}
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Right: Dataset List */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center justify-between gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input
                                type="text"
                                placeholder="Search by filename..."
                                className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-slate-900/10 focus:border-slate-900 transition-all text-slate-900 placeholder:text-slate-400"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-4">
                        {loading ? (
                            <div className="py-20 flex flex-col items-center justify-center">
                                <Loader2 className="w-8 h-8 text-slate-900 animate-spin mb-4" />
                                <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Synchronizing Files...</span>
                            </div>
                        ) : filteredDatasets.length === 0 ? (
                            <Card className="bg-white border-dashed border-2 border-slate-200 text-center py-20 shadow-sm">
                                <FileSpreadsheet className="w-16 h-16 mx-auto mb-4 opacity-20 text-slate-900" />
                                <h3 className="text-lg font-bold mb-1 text-slate-900">No datasets detected</h3>
                                <p className="text-slate-500 text-sm max-w-xs mx-auto mb-6">
                                    Connect your first data source to begin your analytical journey.
                                </p>
                            </Card>
                        ) : (
                            <AnimatePresence>
                                {filteredDatasets.map((dataset, idx) => (
                                    <motion.div
                                        key={dataset.id}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        transition={{ delay: idx * 0.05 }}
                                    >
                                        <Card className="bg-white border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all duration-300 group overflow-hidden">
                                            <CardContent className="p-0">
                                                <div className="flex items-center">
                                                    {/* Preview Icon Column */}
                                                    <div className="w-20 h-24 bg-slate-50 flex flex-col items-center justify-center shrink-0 group-hover:bg-slate-100 transition-colors border-r border-slate-100">
                                                        <FileText className="w-8 h-8 text-slate-400 group-hover:text-slate-900 transition-all duration-300" />
                                                        <span className="text-[8px] font-bold text-slate-400 uppercase mt-1 tracking-tighter">
                                                            {dataset.name.split('.').pop()}
                                                        </span>
                                                    </div>

                                                    {/* Info Column */}
                                                    <div className="flex-1 px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-4">
                                                        <div className="space-y-1">
                                                            <h4 className="font-bold text-lg tracking-tight truncate max-w-[200px] sm:max-w-[300px] text-slate-900">
                                                                {dataset.name}
                                                            </h4>
                                                            <div className="flex items-center gap-4">
                                                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                                                                    <BarChart className="w-3 h-3" /> {(dataset.row_count || 0).toLocaleString()} ROWS
                                                                </span>
                                                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                                                                    <Clock className="w-3 h-3" /> {new Date(dataset.created_at).toLocaleDateString()}
                                                                </span>
                                                            </div>
                                                        </div>

                                                        {/* Status & Actions */}
                                                        <div className="flex items-center gap-4">
                                                            <div className="hidden sm:block">
                                                                {dataset.status === 'processing' ? (
                                                                    <div className="flex items-center gap-2 bg-yellow-50 px-3 py-1 rounded-full border border-yellow-200">
                                                                        <Loader2 className="w-3 h-3 text-yellow-600 animate-spin" />
                                                                        <span className="text-[10px] font-bold text-yellow-600 uppercase tracking-widest">Profiling</span>
                                                                    </div>
                                                                ) : dataset.status === 'error' ? (
                                                                    <div className="flex items-center gap-2 bg-red-50 px-3 py-1 rounded-full border border-red-200">
                                                                        <XCircle className="w-3 h-3 text-red-500" />
                                                                        <span className="text-[10px] font-bold text-red-500 uppercase tracking-widest">Failed</span>
                                                                    </div>
                                                                ) : (
                                                                    <div className="flex items-center gap-2 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                                                                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                                                                        <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-widest">Active</span>
                                                                    </div>
                                                                )}
                                                            </div>

                                                            <div className="flex items-center gap-2">
                                                                <Link to="/analytics" state={{ datasetId: dataset.id }}>
                                                                    <Button variant="outline" size="sm" className="h-9 border-slate-200 text-slate-600 hover:bg-slate-900 hover:border-slate-900 hover:text-white transition-all font-bold text-xs uppercase tracking-widest">
                                                                        Analyze
                                                                    </Button>
                                                                </Link>
                                                                <Button
                                                                    variant="ghost"
                                                                    size="icon"
                                                                    className="h-9 w-9 text-slate-400 hover:text-red-500 hover:bg-red-50"
                                                                    onClick={() => handleDelete(dataset.id)}
                                                                >
                                                                    <Trash2 className="w-4 h-4" />
                                                                </Button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}
