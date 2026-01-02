import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Database, Plus, Trash2, RefreshCw } from 'lucide-react';
import { connectionsAPI } from '../lib/api';

export default function ConnectionsPage() {
    const [connections, setConnections] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [testingId, setTestingId] = useState<number | null>(null);
    const [showAddForm, setShowAddForm] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        type: 'postgres',
        host: '',
        port: '',
        database: '',
        username: '',
        password: '',
    });

    const fetchConnections = async () => {
        try {
            const res = await connectionsAPI.list();
            setConnections(res.data);
        } catch (e) {
            console.error('Failed to fetch connections', e);
        }
    };

    useEffect(() => {
        fetchConnections();
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await connectionsAPI.create(formData);
            setShowAddForm(false);
            setFormData({
                name: '',
                type: 'postgres',
                host: '',
                port: '',
                database: '',
                username: '',
                password: '',
            });
            fetchConnections();
        } catch (e) {
            console.error('Failed to create connection', e);
        } finally {
            setLoading(false);
        }
    };

    const handleTest = async (id: number) => {
        setTestingId(id);
        try {
            const res = await connectionsAPI.test(id);
            if (res.data.success) {
                alert('Connection successful!');
            } else {
                alert('Connection failed: ' + res.data.error);
            }
        } catch (e) {
            alert('Test failed: ' + (e as any).message);
        } finally {
            setTestingId(null);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this connection?')) return;
        try {
            await connectionsAPI.delete(id);
            fetchConnections();
        } catch (e) {
            console.error('Delete failed', e);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-4">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Data Connections</h1>
                        <p className="text-muted-foreground">Manage your external database sources</p>
                    </div>
                </div>
                <Button onClick={() => setShowAddForm(!showAddForm)}>
                    {showAddForm ? 'Cancel' : <><Plus className="w-4 h-4 mr-2" /> Add Connection</>}
                </Button>
            </div>

            {showAddForm && (
                <Card className="border-primary/20 shadow-lg">
                    <CardHeader>
                        <CardTitle>Register New Database</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Name</label>
                                <Input
                                    placeholder="Production DB"
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Type</label>
                                <select
                                    className="w-full p-2 rounded-md border bg-background"
                                    value={formData.type}
                                    onChange={e => setFormData({ ...formData, type: e.target.value })}
                                >
                                    <option value="postgres">PostgreSQL</option>
                                    <option value="mysql">MySQL</option>
                                    <option value="snowflake">Snowflake</option>
                                    <option value="sqlite">SQLite (Path)</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Host / Account</label>
                                <Input
                                    placeholder="localhost or snowflake-account"
                                    value={formData.host}
                                    onChange={e => setFormData({ ...formData, host: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Database / File Path</label>
                                <Input
                                    placeholder="main_db or /path/to/db.sqlite"
                                    value={formData.database}
                                    onChange={e => setFormData({ ...formData, database: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Username</label>
                                <Input
                                    value={formData.username}
                                    onChange={e => setFormData({ ...formData, username: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Password</label>
                                <Input
                                    type="password"
                                    value={formData.password}
                                    onChange={e => setFormData({ ...formData, password: e.target.value })}
                                />
                            </div>
                            <div className="col-span-2 mt-2">
                                <Button type="submit" className="w-full" disabled={loading}>
                                    {loading ? 'Saving...' : 'Save Connection'}
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            )}

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {connections.map(conn => (
                    <Card key={conn.id} className="group hover:border-primary/50 transition-all">
                        <CardContent className="pt-6">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-primary/10 rounded-lg">
                                        <Database className="w-5 h-5 text-primary" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold">{conn.name}</h3>
                                        <p className="text-xs text-muted-foreground uppercase">{conn.type}</p>
                                    </div>
                                </div>
                                <Button variant="ghost" size="sm" onClick={() => handleDelete(conn.id)} className="opacity-0 group-hover:opacity-100 text-destructive hover:bg-destructive/10">
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            </div>
                            <div className="space-y-1 text-sm text-muted-foreground mb-4">
                                <p>Host: {conn.host || 'N/A'}</p>
                                <p>Database: {conn.database}</p>
                            </div>
                            <Button
                                variant="secondary"
                                className="w-full text-xs h-8"
                                onClick={() => handleTest(conn.id)}
                                disabled={testingId === conn.id}
                            >
                                {testingId === conn.id ? (
                                    <RefreshCw className="w-3 h-3 mr-2 animate-spin" />
                                ) : 'Test Connection'}
                            </Button>
                        </CardContent>
                    </Card>
                ))}
                {connections.length === 0 && !showAddForm && (
                    <div className="col-span-full py-12 text-center border-2 border-dashed rounded-xl">
                        <Database className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                        <h3 className="text-lg font-medium">No connections yet</h3>
                        <p className="text-muted-foreground mb-4">Add your first database source to start querying.</p>
                        <Button variant="outline" onClick={() => setShowAddForm(true)}>Add Connection</Button>
                    </div>
                )}
            </div>
        </div>
    );
}
