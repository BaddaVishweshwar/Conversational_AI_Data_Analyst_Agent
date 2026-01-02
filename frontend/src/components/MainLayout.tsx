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
            <div className={`${sidebarCollapsed ? 'w-0' : 'w-48'} transition-all duration-300 border-r border-border bg-background flex flex-col overflow-hidden`}>
                {/* Navigation */}
                <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-2.5 px-3 py-2 rounded-md transition-all text-sm ${isActive
                                    ? 'bg-muted text-foreground'
                                    : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                                    }`}
                            >
                                <Icon className="w-4 h-4 shrink-0" />
                                <span>{item.name}</span>
                            </Link>
                        );
                    })}

                    {/* DATASETS Section */}
                    <div className="pt-6">
                        <div className="px-3 pb-2 text-[10px] font-semibold text-muted-foreground/70 uppercase tracking-wider">
                            Datasets
                        </div>
                        <div className="space-y-0.5">
                            {datasets.map((dataset) => (
                                <div key={dataset.id} className="group relative">
                                    <Link
                                        to="/datasets"
                                        className="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all pr-8"
                                    >
                                        <Database className="w-4 h-4 shrink-0" />
                                        <span className="truncate">{dataset.name}</span>
                                    </Link>
                                    <button
                                        onClick={() => handleDeleteDataset(dataset.id)}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 rounded opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-destructive hover:text-white text-muted-foreground"
                                        title="Delete dataset"
                                    >
                                        <span className="text-xs">×</span>
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </nav>

                {/* Sidebar Footer */}
                <div className="border-t border-border p-2 space-y-0.5">
                    <Link
                        to="/settings"
                        className="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all"
                    >
                        <Settings className="w-4 h-4 shrink-0" />
                        <span>Settings</span>
                    </Link>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all"
                    >
                        <LogOut className="w-4 h-4 shrink-0" />
                        <span>Logout</span>
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
                        <Button variant="ghost" size="sm" className="p-1.5 h-auto">
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
        </div>
    );
}
