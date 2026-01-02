import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    BarChart3,
    Database,
    Network,
    Zap,
    BrainCircuit,
    LogOut,
    ChevronLeft,
    ChevronRight,
    Settings,
    History as HistoryIcon,
    Shield,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { Button } from './ui/button';
import { useState } from 'react';
import { cn } from '../lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'History', href: '/history', icon: HistoryIcon },
    { name: 'Datasets', href: '/datasets', icon: Database },
    { name: 'Connections', href: '/connections', icon: Network },
];

export default function Sidebar() {
    const location = useLocation();
    const logout = useAuthStore((state) => state.logout);
    const user = useAuthStore((state) => state.user);
    const [collapsed, setCollapsed] = useState(false);

    return (
        <aside
            className={cn(
                "h-screen bg-slate-50 border-r border-slate-200 transition-all duration-500 flex flex-col z-50 relative shrink-0",
                collapsed ? "w-20" : "w-72"
            )}
        >
            {/* Logo Section */}
            <div className="p-8 flex items-center justify-between">
                <Link to="/" className="flex items-center gap-3 overflow-hidden group">
                    <div className="w-10 h-10 rounded-lg bg-slate-900 flex-shrink-0 flex items-center justify-center shadow-sm group-hover:bg-black transition-all duration-300">
                        <BarChart3 className="w-5 h-5 text-white" />
                    </div>
                    {!collapsed && (
                        <motion.span
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="font-bold text-xl tracking-tight whitespace-nowrap text-slate-900"
                        >
                            Antigravity
                        </motion.span>
                    )}
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-4 space-y-1.5 mt-2 overflow-y-auto custom-scrollbar">
                {[
                    ...navigation,
                    ...(user?.is_admin ? [{ name: 'Admin', href: '/admin', icon: Shield }] : [])
                ].map((item) => {
                    const isActive = location.pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            to={item.href}
                            className={cn(
                                "flex items-center gap-4 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200",
                                isActive
                                    ? "bg-white text-slate-900 shadow-sm border border-slate-200"
                                    : "text-slate-500 hover:bg-slate-200/50 hover:text-slate-900"
                            )}
                        >
                            <item.icon className={cn(
                                "w-4 h-4 flex-shrink-0",
                                isActive ? "text-slate-900" : "text-slate-400 group-hover:text-slate-900"
                            )} />
                            {!collapsed && (
                                <motion.span
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="text-sm"
                                >
                                    {item.name}
                                </motion.span>
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Footer / User Profile */}
            <div className="p-6 border-t border-slate-200 bg-slate-100/30">
                <AnimatePresence>
                    {!collapsed && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 10 }}
                            className="mb-6 px-2"
                        >
                            <div className="flex items-center gap-4 p-2.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                                <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-xs font-bold text-slate-700 shrink-0">
                                    {user?.username?.[0].toUpperCase() || 'U'}
                                </div>
                                <div className="overflow-hidden">
                                    <p className="text-xs font-bold truncate text-slate-900">{user?.username || 'Guest'}</p>
                                    <p className="text-[10px] text-slate-500 truncate uppercase tracking-wider">Free Plan</p>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="space-y-1">
                    <Button
                        variant="ghost"
                        size={collapsed ? "icon" : "sm"}
                        className={cn(
                            "w-full justify-start gap-4 text-slate-500 hover:text-slate-900 hover:bg-slate-200/50 rounded-lg h-10 px-4 transition-all",
                            collapsed && "justify-center"
                        )}
                    >
                        <Settings className="w-4 h-4 flex-shrink-0" />
                        {!collapsed && <span className="text-sm">Settings</span>}
                    </Button>
                    <button
                        onClick={logout}
                        className={cn(
                            "w-full flex items-center justify-start gap-4 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg h-10 px-4 transition-all group",
                            collapsed && "justify-center"
                        )}
                    >
                        <LogOut className="w-4 h-4 flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
                        {!collapsed && <span className="text-sm">Logout</span>}
                    </button>
                </div>
            </div>

            {/* Collapse Toggle */}
            <button
                onClick={() => setCollapsed(!collapsed)}
                className="absolute -right-3 top-24 w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-900 hover:scale-110 transition-all z-50 shadow-sm"
            >
                {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
            </button>
        </aside>
    );
}
