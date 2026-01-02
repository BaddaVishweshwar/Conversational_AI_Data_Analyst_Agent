import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import {
    MessageSquare,
    LayoutDashboard,
    History,
    BookmarkPlus,
    Settings,
    LogOut,
    Database,
    User,
    Plus,
    RefreshCw,
    Grid3x3,
    ChevronLeft
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { datasetsAPI } from '../lib/api';
import { Button } from './ui/button';

interface NavItem {
    name: string;
    icon: any;
    path: string;
}

interface MainLayoutProps {
    children?: React.ReactNode;
}

const navItems: NavItem[] = [
    { name: 'Chat', icon: MessageSquare, path: '/analytics' },
    { name: 'Dashboards', icon: LayoutDashboard, path: '/dashboard' },
    { name: 'History', icon: History, path: '/history' },
    { name: 'Saved Insights', icon: BookmarkPlus, path: '/saved' },
];

export default function MainLayout({ children }: MainLayoutProps) {
    const { logout } = useAuthStore();
    const navigate = useNavigate();
    const location = useLocation();
    const [datasets, setDatasets] = useState<any[]>([]);
    const [selectedDataset, setSelectedDataset] = useState<number | null>(null);
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [showDatasetsModal, setShowDatasetsModal] = useState(false);

    useEffect(() => {
        loadDatasets();
    }, []);

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

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handleDeleteDataset = async (datasetId: number) => {
        if (confirm('Are you sure you want to delete this dataset?')) {
            try {
                await datasetsAPI.delete(datasetId);
                await loadDatasets();
                if (selectedDataset === datasetId) {
                    setSelectedDataset(datasets.length > 1 ? datasets[0].id : null);
                }
            } catch (error) {
                console.error('Error deleting dataset:', error);
                alert('Failed to delete dataset');
            }
        }
    };

    return (
        <div className="flex h-screen bg-background overflow-hidden">
            {/* Left Sidebar */}
            <div className={`${sidebarCollapsed ? 'w-0' : 'w-60'} transition-all duration-300 border-r border-border bg-background flex flex-col overflow-hidden`}>
                {/* Navigation */}
                <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all ${isActive
                                    ? 'bg-muted text-foreground'
                                    : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                                    }`}
                            >
                                <Icon className="w-5 h-5 shrink-0" />
                                <span className="text-sm font-medium">{item.name}</span>
                            </Link>
                        );
                    })}

                    {/* DATASETS Section */}
                    <div className="pt-6">
                        <div className="px-4 pb-2.5 text-[11px] font-semibold text-muted-foreground/60 uppercase tracking-wide">
                            Datasets
                        </div>
                        <div className="space-y-1">
                            {datasets.map((dataset) => (
                                <div key={dataset.id} className="group relative">
                                    <Link
                                        to="/datasets"
                                        className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all pr-9"
                                    >
                                        <Database className="w-5 h-5 shrink-0" />
                                        <span className="truncate font-medium">{dataset.name}</span>
                                    </Link>
                                    <button
                                        onClick={() => handleDeleteDataset(dataset.id)}
                                        className="absolute right-2.5 top-1/2 -translate-y-1/2 w-5 h-5 rounded opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-destructive hover:text-white text-muted-foreground"
                                        title="Delete dataset"
                                    >
                                        <span className="text-sm">×</span>
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </nav>

                {/* Sidebar Footer */}
                <div className="border-t border-border p-3 space-y-1">
                    <Link
                        to="/settings"
                        className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all"
                    >
                        <Settings className="w-5 h-5 shrink-0" />
                        <span className="font-medium">Settings</span>
                    </Link>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all"
                    >
                        <LogOut className="w-5 h-5 shrink-0" />
                        <span className="font-medium">Logout</span>
                    </button>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Top Bar */}
                <div className="h-12 border-b border-border flex items-center justify-between px-3 bg-background">
                    {/* Left: AI Analyst + Collapse + Dataset Tabs */}
                    <div className="flex items-center gap-2 flex-1">
                        <button
                            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                            className="p-1.5 hover:bg-muted rounded-md transition-colors"
                        >
                            <ChevronLeft className={`w-4 h-4 text-muted-foreground transition-transform ${sidebarCollapsed ? 'rotate-180' : ''}`} />
                        </button>
                        <span className="text-sm font-semibold text-foreground px-2">AI Analyst</span>

                        {/* Dataset Tabs */}
                        <div className="flex items-center gap-1.5 ml-2">
                            {datasets.slice(0, 3).map((dataset, idx) => {
                                const colors = ['text-accent', 'text-orange-500', 'text-purple-500'];
                                const isSelected = selectedDataset === dataset.id;
                                return (
                                    <div key={dataset.id} className="group relative">
                                        <button
                                            onClick={() => setSelectedDataset(dataset.id)}
                                            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-colors ${isSelected
                                                ? 'bg-muted text-foreground border border-border'
                                                : 'text-muted-foreground hover:bg-muted'
                                                }`}
                                        >
                                            <Database className={`w-3 h-3 ${colors[idx]}`} />
                                            <span>{dataset.name}</span>
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteDataset(dataset.id);
                                            }}
                                            className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-muted border border-border opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-destructive hover:text-white"
                                        >
                                            <span className="text-[10px]">×</span>
                                        </button>
                                    </div>
                                );
                            })}
                            <Link to="/datasets">
                                <Button variant="ghost" size="sm" className="h-7 px-2 text-xs text-muted-foreground">
                                    <Plus className="w-3.5 h-3.5 mr-1" />
                                    Add Dataset
                                </Button>
                            </Link>
                        </div>
                    </div>

                    {/* Right Controls */}
                    <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" className="p-1.5 h-auto">
                            <Settings className="w-4 h-4 text-muted-foreground" />
                        </Button>
                        <Button variant="ghost" size="sm" className="p-1.5 h-auto">
                            <RefreshCw className="w-4 h-4 text-muted-foreground" />
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="p-1.5 h-auto"
                            onClick={() => {
                                if (selectedDataset) {
                                    navigate(`/data-view?dataset=${selectedDataset}`);
                                } else if (datasets.length > 0) {
                                    navigate(`/data-view?dataset=${datasets[0].id}`);
                                }
                            }}
                        >
                            <Grid3x3 className="w-4 h-4 text-muted-foreground" />
                        </Button>
                        <Link to="/settings">
                            <button className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center ml-1">
                                <User className="w-3.5 h-3.5 text-accent" />
                            </button>
                        </Link>
                    </div>
                </div>

                {/* Page Content */}
                <main className="flex-1 overflow-hidden">
                    {children || <Outlet />}
                </main>
            </div>

            {/* Datasets Modal */}
            {showDatasetsModal && (
                <div
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                    onClick={() => setShowDatasetsModal(false)}
                >
                    <div
                        className="bg-card border border-border rounded-xl max-w-4xl w-full max-h-[80vh] overflow-hidden shadow-2xl"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Modal Header */}
                        <div className="border-b border-border px-6 py-4 flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-semibold text-foreground">All Datasets</h2>
                                <p className="text-sm text-muted-foreground mt-0.5">
                                    {datasets.length} dataset{datasets.length !== 1 ? 's' : ''} uploaded
                                </p>
                            </div>
                            <button
                                onClick={() => setShowDatasetsModal(false)}
                                className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors"
                            >
                                <span className="text-xl text-muted-foreground">×</span>
                            </button>
                        </div>

                        {/* Modal Content */}
                        <div className="overflow-y-auto max-h-[calc(80vh-80px)]">
                            {datasets.length === 0 ? (
                                <div className="text-center py-16">
                                    <Database className="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
                                    <p className="text-muted-foreground">No datasets uploaded yet</p>
                                    <Link to="/datasets">
                                        <Button className="mt-4 bg-accent hover:bg-accent/90">
                                            <Plus className="w-4 h-4 mr-2" />
                                            Upload Dataset
                                        </Button>
                                    </Link>
                                </div>
                            ) : (
                                <div className="divide-y divide-border">
                                    {datasets.map((dataset) => (
                                        <div
                                            key={dataset.id}
                                            className="px-6 py-4 hover:bg-muted/30 transition-colors group"
                                        >
                                            <div className="flex items-start justify-between">
                                                <div className="flex items-start gap-3 flex-1">
                                                    <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center shrink-0 mt-0.5">
                                                        <Database className="w-5 h-5 text-accent" />
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <h3 className="font-medium text-foreground mb-1">{dataset.name}</h3>
                                                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                                            <span>{dataset.row_count?.toLocaleString() || 0} rows</span>
                                                            <span>•</span>
                                                            <span>{dataset.column_count || 0} columns</span>
                                                            <span>•</span>
                                                            <span>{new Date(dataset.created_at).toLocaleDateString()}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        className="h-8"
                                                        onClick={() => {
                                                            setSelectedDataset(dataset.id);
                                                            setShowDatasetsModal(false);
                                                            navigate('/analytics');
                                                        }}
                                                    >
                                                        Analyze
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                                                        onClick={() => handleDeleteDataset(dataset.id)}
                                                    >
                                                        Delete
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
