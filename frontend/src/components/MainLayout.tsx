import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import {
    MessageSquare,
    LayoutDashboard,
    History,
    BookmarkPlus,
    Settings,
    LogOut,
    ChevronLeft,
    ChevronRight,
    Database,
    User
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
];

export default function MainLayout() {
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();
    const location = useLocation();
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [datasets, setDatasets] = useState<any[]>([]);
    const [selectedDataset, setSelectedDataset] = useState<number | null>(null);

    useEffect(() => {
        loadDatasets();
    }, []);

    const loadDatasets = async () => {
        try {
            const response = await datasetsAPI.list();
            setDatasets(response.data);
            if (response.data.length > 0) {
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
            {/* Left Sidebar - Collapsible */}
            <div
                className={`${sidebarOpen ? 'w-64' : 'w-16'
                    } transition-all duration-300 border-r border-border bg-card flex flex-col`}
            >
                {/* Sidebar Header */}
                <div className="h-16 border-b border-border flex items-center justify-between px-4">
                    {sidebarOpen && (
                        <h1 className="text-lg font-semibold text-foreground">AI Analyst</h1>
                    )}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="p-2"
                    >
                        {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </Button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-6 px-2 space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`
                  flex items-center gap-3 px-3 py-2 rounded-lg transition-all
                  ${isActive
                                        ? 'bg-accent/10 text-accent'
                                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                    }
                  ${!sidebarOpen && 'justify-center'}
                `}
                            >
                                <Icon className="w-5 h-5 shrink-0" />
                                {sidebarOpen && <span className="text-sm font-medium">{item.name}</span>}
                            </Link>
                        );
                    })}
                </nav>

                {/* Sidebar Footer */}
                <div className="border-t border-border p-2 space-y-1">
                    <Link
                        to="/settings"
                        className={`
              flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-all
              ${!sidebarOpen && 'justify-center'}
            `}
                    >
                        <Settings className="w-5 h-5 shrink-0" />
                        {sidebarOpen && <span className="text-sm font-medium">Settings</span>}
                    </Link>
                    <button
                        onClick={handleLogout}
                        className={`
              w-full flex items-center gap-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-all
              ${!sidebarOpen && 'justify-center'}
            `}
                    >
                        <LogOut className="w-5 h-5 shrink-0" />
                        {sidebarOpen && <span className="text-sm font-medium">Logout</span>}
                    </button>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Top Navbar - Sticky */}
                <div className="h-16 border-b border-border flex items-center justify-between px-6 glass sticky top-0 z-10">
                    {/* Left: Product Logo */}
                    <Link to="/" className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                            <Database className="w-5 h-5 text-accent" />
                        </div>
                        <span className="text-sm font-semibold text-foreground">AI Data Analyst</span>
                    </Link>

                    {/* Center: Dataset Selector (Pill Style) */}
                    <div className="flex-1 max-w-md mx-auto">
                        <select
                            value={selectedDataset || ''}
                            onChange={(e) => setSelectedDataset(Number(e.target.value))}
                            className="w-full px-4 py-2 bg-muted border border-border rounded-full text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20"
                        >
                            <option value="">Select Dataset...</option>
                            {datasets.map((dataset) => (
                                <option key={dataset.id} value={dataset.id}>
                                    {dataset.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Right: User Controls */}
                    <div className="flex items-center gap-4">
                        <Link to="/settings">
                            <Button variant="ghost" size="sm" className="p-2">
                                <Settings className="w-5 h-5" />
                            </Button>
                        </Link>
                        <button className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
                            <User className="w-4 h-4 text-accent" />
                        </button>
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
