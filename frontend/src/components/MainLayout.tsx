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
    FolderOpen,
    Plus,
    RefreshCw,
    Grid3x3
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
            <div className="w-64 border-r border-border bg-background flex flex-col">
                {/* Sidebar Header */}
                <div className="h-14 border-b border-border flex items-center px-4">
                    <h1 className="text-lg font-semibold text-foreground">AI Analyst</h1>
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-sm ${isActive
                                    ? 'bg-accent/10 text-accent'
                                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                    }`}
                            >
                                <Icon className="w-4 h-4 shrink-0" />
                                <span className="font-medium">{item.name}</span>
                            </Link>
                        );
                    })}

                    {/* DATASETS Section */}
                    <div className="pt-4">
                        <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            Datasets
                        </div>
                        <div className="space-y-1">
                            {datasets.map((dataset) => (
                                <Link
                                    key={dataset.id}
                                    to={`/datasets`}
                                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-all"
                                >
                                    <Database className="w-4 h-4 shrink-0" />
                                    <span className="truncate">{dataset.name}</span>
                                </Link>
                            ))}
                        </div>
                    </div>
                </nav>

                {/* Sidebar Footer */}
                <div className="border-t border-border p-3 space-y-1">
                    <Link
                        to="/settings"
                        className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-all"
                    >
                        <Settings className="w-4 h-4 shrink-0" />
                        <span className="font-medium">Settings</span>
                    </Link>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-all"
                    >
                        <LogOut className="w-4 h-4 shrink-0" />
                        <span className="font-medium">Logout</span>
                    </button>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Top Navbar with Dataset Tabs */}
                <div className="h-14 border-b border-border flex items-center justify-between px-4 bg-background">
                    {/* Dataset Tabs */}
                    <div className="flex items-center gap-2 flex-1 overflow-x-auto">
                        {datasets.slice(0, 3).map((dataset) => (
                            <button
                                key={dataset.id}
                                onClick={() => setSelectedDataset(dataset.id)}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all whitespace-nowrap ${selectedDataset === dataset.id
                                    ? 'bg-accent/10 text-accent border border-accent/20'
                                    : 'text-muted-foreground hover:bg-muted border border-transparent'
                                    }`}
                            >
                                <Database className="w-3.5 h-3.5" />
                                <span>{dataset.name}</span>
                            </button>
                        ))}
                        <Link to="/datasets">
                            <Button
                                variant="ghost"
                                size="sm"
                                className="text-muted-foreground hover:text-foreground"
                            >
                                <Plus className="w-4 h-4 mr-1" />
                                Add Dataset
                            </Button>
                        </Link>
                    </div>

                    {/* Right Controls */}
                    <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" className="p-2">
                            <Settings className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="p-2">
                            <RefreshCw className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="p-2">
                            <Grid3x3 className="w-4 h-4" />
                        </Button>
                        <Link to="/settings">
                            <button className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center">
                                <User className="w-4 h-4 text-accent" />
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
