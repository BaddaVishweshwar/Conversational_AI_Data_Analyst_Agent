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

const navItems: NavItem[] = [
    { name: 'Chat', icon: MessageSquare, path: '/analytics' },
    { name: 'Dashboards', icon: LayoutDashboard, path: '/dashboard' },
    { name: 'History', icon: History, path: '/history' },
    { name: 'Saved Insights', icon: BookmarkPlus, path: '/saved' },
];

export default function MainLayout() {
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
                            <Link
                                to="/datasets"
                                className="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all"
                            >
                                <Database className="w-4 h-4 shrink-0" />
                                <span>Advertising.csv</span>
                            </Link>
                            <Link
                                to="/datasets"
                                className="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all"
                            >
                                <Database className="w-4 h-4 shrink-0" />
                                <span>Sales.csv</span>
                            </Link>
                            <Link
                                to="/datasets"
                                className="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all"
                            >
                                <Database className="w-4 h-4 shrink-0" />
                                <span>Customers.csv</span>
                            </Link>
                            {datasets.slice(3).map((dataset) => (
                                <Link
                                    key={dataset.id}
                                    to="/datasets"
                                    className="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-all"
                                >
                                    <Database className="w-4 h-4 shrink-0" />
                                    <span className="truncate">{dataset.name}</span>
                                </Link>
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
                            <button className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs bg-muted text-foreground border border-border">
                                <Database className="w-3 h-3 text-accent" />
                                Advertising.csv
                            </button>
                            <button className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs text-muted-foreground hover:bg-muted transition-colors">
                                <Database className="w-3 h-3 text-orange-500" />
                                Sales.csv
                            </button>
                            <button className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs text-muted-foreground hover:bg-muted transition-colors">
                                <Database className="w-3 h-3 text-purple-500" />
                                Customers.csv
                            </button>
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
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
