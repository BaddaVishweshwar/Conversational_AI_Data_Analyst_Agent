import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import {
    BarChart3,
    Database,
    Upload,
    ExternalLink,
    Zap,
    ArrowUpRight,
    Search,
    Plus,
    Network,
    XCircle
} from 'lucide-react';
import { datasetsAPI, queriesAPI, dashboardsAPI, connectionsAPI } from '../lib/api';
import ChartRenderer from '../components/ChartRenderer';
import { motion } from 'framer-motion';

export default function DashboardPage() {
    const [datasets, setDatasets] = useState<any[]>([]);
    const [recentQueries, setRecentQueries] = useState<any[]>([]);
    const [dashboards, setDashboards] = useState<any[]>([]);
    const [connections, setConnections] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            const [datasetsRes, queriesRes, dashRes, connRes] = await Promise.all([
                datasetsAPI.list(),
                queriesAPI.history(5),
                dashboardsAPI.list(),
                connectionsAPI.list()
            ]);
            setDatasets(datasetsRes.data);
            setRecentQueries(queriesRes.data);
            setDashboards(dashRes.data);
            setConnections(connRes.data);
        } catch (error) {
            console.error('Error loading dashboard:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-[80vh]">
                <div className="relative w-16 h-16">
                    <div className="absolute top-0 left-0 w-full h-full border-4 border-primary/20 rounded-full animate-pulse"></div>
                    <div className="absolute top-0 left-0 w-full h-full border-t-4 border-primary rounded-full animate-spin"></div>
                </div>
                <p className="mt-4 text-muted-foreground animate-pulse font-medium">Preparing your workspace...</p>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header / Welcome Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                        Dashboard
                    </h1>
                    <p className="text-slate-500 mt-1">
                        Overview of your workspace and recent analytical activity.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <Link to="/analytics">
                        <Button className="bg-slate-900 hover:bg-black text-white rounded-lg px-6 gap-2 h-10 shadow-sm transition-all active:scale-95">
                            <Plus className="w-4 h-4" /> New Analysis
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                    { label: "Datasets", value: datasets.length, icon: Database, color: "text-slate-900" },
                    { label: "Analyses", value: recentQueries.length, icon: BarChart3, color: "text-slate-900" },
                    { label: "Success Rate", value: recentQueries.length > 0 ? `${Math.round((recentQueries.filter(q => q.status === 'success').length / recentQueries.length) * 100)}%` : '0%', icon: Zap, color: "text-slate-900" },
                    { label: "Connections", value: connections.length, icon: Network, color: "text-slate-900" }
                ].map((stat, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.05 }}
                    >
                        <Card className="bg-white border-slate-200 shadow-sm hover:shadow-md transition-shadow duration-300">
                            <CardContent className="p-6">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                                        <stat.icon className={`h-4 w-4 ${stat.color}`} />
                                    </div>
                                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{stat.label}</p>
                                </div>
                                <div className="text-2xl font-bold tracking-tight text-slate-900">{stat.value}</div>
                            </CardContent>
                        </Card>
                    </motion.div>
                ))}
            </div>

            {/* Main Content Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Left Side: Recent Activity & Dashboards (2/3) */}
                <div className="lg:col-span-2 space-y-8">

                    {/* Active Insights / Widgets */}
                    <div>
                        <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
                            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                                Pinned Insights
                            </h2>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {dashboards[0]?.widgets?.length > 0 ? (
                                dashboards[0].widgets.map((widget: any, widx: number) => {
                                    const isFullWidth = widget.layout === 'full';
                                    return (
                                        <motion.div
                                            key={widx}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: widx * 0.1 }}
                                            className={`${isFullWidth ? 'lg:col-span-2' : ''}`}
                                        >
                                            <Card className="bg-white border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
                                                <CardHeader className="py-3 px-5 border-b border-slate-50 flex flex-row items-center justify-between bg-slate-50/30">
                                                    <div className="flex flex-col">
                                                        <CardTitle className="text-sm font-bold text-slate-900">
                                                            {widget.title}
                                                        </CardTitle>
                                                    </div>
                                                    <div className="flex items-center gap-1">
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="h-8 w-8 p-0 text-slate-400 hover:text-slate-900"
                                                            onClick={async () => {
                                                                if (!confirm('Remove this widget?')) return;

                                                                const newWidgets = dashboards[0].widgets.filter((_: any, i: number) => i !== widx);
                                                                const updatedDashboard = { ...dashboards[0], widgets: newWidgets };
                                                                const newDashboards = [...dashboards];
                                                                newDashboards[0] = updatedDashboard;

                                                                setDashboards(newDashboards);
                                                                try {
                                                                    await dashboardsAPI.update(dashboards[0].id, {
                                                                        widgets: newWidgets
                                                                    });
                                                                } catch (e) { console.error("Failed to remove widget", e); }
                                                            }}
                                                        >
                                                            <XCircle className="w-4 h-4" />
                                                        </Button>
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="h-8 w-8 p-0 text-slate-400 hover:text-slate-900"
                                                            onClick={async () => {
                                                                const newLayout = isFullWidth ? 'half' : 'full';
                                                                const newDashboards = [...dashboards];
                                                                newDashboards[0].widgets[widx].layout = newLayout;
                                                                setDashboards(newDashboards);
                                                                try {
                                                                    await dashboardsAPI.update(dashboards[0].id, {
                                                                        widgets: newDashboards[0].widgets
                                                                    });
                                                                } catch (e) {
                                                                    console.error("Failed to save layout", e);
                                                                }
                                                            }}
                                                        >
                                                            <ArrowUpRight className="w-4 h-4" />
                                                        </Button>
                                                    </div>
                                                </CardHeader>
                                                <CardContent className="p-6 flex-1 bg-white">
                                                    {widget.python_chart ? (
                                                        <img src={widget.python_chart} className="w-full h-auto rounded-lg border border-slate-100" alt={widget.title} />
                                                    ) : widget.viz_config ? (
                                                        <div className="w-full min-h-[250px] flex items-center justify-center">
                                                            <ChartRenderer config={widget.viz_config} />
                                                        </div>
                                                    ) : (
                                                        <div className="w-full p-4 bg-slate-50 rounded-lg text-xs font-mono border border-slate-100 text-slate-600 overflow-x-auto">
                                                            {widget.sql}
                                                        </div>
                                                    )}
                                                </CardContent>
                                            </Card>
                                        </motion.div>
                                    );
                                })
                            ) : (
                                <div className="lg:col-span-2 p-12 text-center bg-white rounded-xl border border-dashed border-slate-200">
                                    <BarChart3 className="w-12 h-12 mx-auto mb-4 text-slate-200" />
                                    <h3 className="text-base font-bold text-slate-900 mb-1">No pinned insights</h3>
                                    <p className="text-slate-500 text-sm max-w-xs mx-auto mb-6">
                                        Analyze your datasets and pin key insights here for quick access.
                                    </p>
                                    <Link to="/analytics">
                                        <Button variant="outline" size="sm" className="border-slate-200 text-slate-700 hover:bg-slate-50">
                                            Start Analyzing
                                        </Button>
                                    </Link>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Recent Datasets Section */}
                    <div>
                        <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
                            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                                Inventory
                            </h2>
                            <Link to="/datasets" className="text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors">
                                View All
                            </Link>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {datasets.slice(0, 4).map((dataset) => (
                                <Card key={dataset.id} className="bg-white border-slate-200 hover:border-slate-400 shadow-sm transition-all duration-300 group">
                                    <CardContent className="p-4 flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-lg bg-slate-50 flex items-center justify-center border border-slate-100 group-hover:bg-slate-100 transition-colors">
                                                <Database className="w-5 h-5 text-slate-400 group-hover:text-slate-900 transition-colors" />
                                            </div>
                                            <div>
                                                <div className="font-bold text-sm text-slate-900">{dataset.name}</div>
                                                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                                                    {dataset.row_count?.toLocaleString()} rows
                                                </div>
                                            </div>
                                        </div>
                                        <Link to="/analytics" state={{ datasetId: dataset.id }}>
                                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-full text-slate-400 hover:text-slate-900">
                                                <ExternalLink className="w-4 h-4" />
                                            </Button>
                                        </Link>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right Side: Quick Actions & Recent Queries (1/3) */}
                <div className="space-y-8">

                    {/* Quick Actions Card */}
                    <Card className="bg-slate-900 text-white shadow-xl">
                        <CardHeader className="p-6 pb-2">
                            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                                Actions
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-6 pt-2 space-y-2">
                            <Link to="/datasets">
                                <Button className="w-full justify-start gap-3 bg-white/10 hover:bg-white/20 text-white border-none text-sm h-11 transition-all">
                                    <Upload className="w-4 h-4" />
                                    Import Dataset
                                </Button>
                            </Link>
                            <Link to="/analytics">
                                <Button className="w-full justify-start gap-3 bg-white/10 hover:bg-white/20 text-white border-none text-sm h-11 transition-all">
                                    <Search className="w-4 h-4" />
                                    Explore Data
                                </Button>
                            </Link>
                            <Link to="/connections">
                                <Button className="w-full justify-start gap-3 bg-white/10 hover:bg-white/20 text-white border-none text-sm h-11 transition-all">
                                    <Network className="w-4 h-4" />
                                    Configure Sources
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>

                    {/* Recent Queries Feed */}
                    <div className="bg-slate-50/50 p-6 rounded-2xl border border-slate-100">
                        <h2 className="text-sm font-bold text-slate-900 mb-6 flex items-center gap-2">
                            Intelligence Log
                        </h2>
                        <div className="space-y-6">
                            {recentQueries.length > 0 ? (
                                recentQueries.map((query) => (
                                    <div key={query.id} className="relative pl-6 last:pb-0 group">
                                        <div className="absolute left-[3px] top-1.5 w-[1px] h-full bg-slate-200 group-last:hidden" />
                                        <div className={`absolute left-0 top-1.5 w-2 h-2 rounded-full ${query.status === 'success' ? 'bg-slate-900' : 'bg-red-500'}`} />

                                        <div className="space-y-1">
                                            <p className="text-xs font-medium text-slate-900 leading-relaxed line-clamp-2">
                                                {query.natural_language_query}
                                            </p>
                                            <div className="flex items-center gap-3">
                                                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">
                                                    {query.status}
                                                </span>
                                                <span className="text-[10px] text-slate-400">
                                                    {new Date(query.created_at).toLocaleDateString()}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="text-xs text-slate-400 italic text-center p-4">
                                    No recent logs found
                                </p>
                            )}
                        </div>
                    </div>
                </div>

            </div>
        </div >
    );
}
