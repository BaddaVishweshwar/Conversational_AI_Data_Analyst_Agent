import { User, Mail, Shield } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { api } from '../lib/api';

export default function SettingsPage() {
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('profile');

    useEffect(() => {
        loadUser();
    }, []);

    const loadUser = async () => {
        try {
            const response = await api.get('/auth/me');
            setUser(response.data);
        } catch (error) {
            console.error('Error loading user:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent"></div>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto bg-background">
            <div className="max-w-5xl mx-auto px-6 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-semibold text-foreground mb-2">Settings</h1>
                    <p className="text-muted-foreground">Manage your account settings and preferences</p>
                </div>

                {/* Tabs */}
                <div className="border-b border-border mb-8">
                    <div className="flex gap-6">
                        {[
                            { id: 'profile', label: 'Profile', icon: User },
                            { id: 'account', label: 'Account', icon: Mail },
                            { id: 'security', label: 'Security', icon: Shield },
                        ].map((tab) => {
                            const Icon = tab.icon;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${activeTab === tab.id
                                            ? 'border-accent text-accent'
                                            : 'border-transparent text-muted-foreground hover:text-foreground'
                                        }`}
                                >
                                    <Icon className="w-4 h-4" />
                                    <span className="text-sm font-medium">{tab.label}</span>
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Content */}
                <div className="space-y-6">
                    {activeTab === 'profile' && (
                        <div className="space-y-6">
                            <div className="bg-card border border-border rounded-lg p-6">
                                <h2 className="text-lg font-semibold text-foreground mb-4">Profile Information</h2>

                                <div className="space-y-4">
                                    <div>
                                        <label className="text-sm font-medium text-foreground mb-1.5 block">
                                            Username
                                        </label>
                                        <Input
                                            type="text"
                                            value={user?.username || ''}
                                            disabled
                                            className="bg-muted border-border"
                                        />
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium text-foreground mb-1.5 block">
                                            Email
                                        </label>
                                        <Input
                                            type="email"
                                            value={user?.email || ''}
                                            disabled
                                            className="bg-muted border-border"
                                        />
                                    </div>

                                    <p className="text-xs text-muted-foreground">
                                        Contact support to change your username or email
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'account' && (
                        <div className="space-y-6">
                            <div className="bg-card border border-border rounded-lg p-6">
                                <h2 className="text-lg font-semibold text-foreground mb-4">Account Details</h2>

                                <div className="space-y-4">
                                    <div className="flex items-center justify-between py-3 border-b border-border">
                                        <div>
                                            <p className="text-sm font-medium text-foreground">Account Status</p>
                                            <p className="text-xs text-muted-foreground">Your account is active</p>
                                        </div>
                                        <span className="text-xs px-3 py-1 rounded-full bg-accent/10 text-accent">
                                            Active
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between py-3">
                                        <div>
                                            <p className="text-sm font-medium text-foreground">Account Type</p>
                                            <p className="text-xs text-muted-foreground">
                                                {user?.is_admin ? 'Administrator' : 'Standard User'}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'security' && (
                        <div className="space-y-6">
                            <div className="bg-card border border-border rounded-lg p-6">
                                <h2 className="text-lg font-semibold text-foreground mb-4">Password</h2>

                                <div className="space-y-4">
                                    <p className="text-sm text-muted-foreground mb-4">
                                        Change your password to keep your account secure
                                    </p>

                                    <Button
                                        onClick={() => window.location.href = '/forgot-password'}
                                        variant="outline"
                                        className="w-full sm:w-auto border-border"
                                    >
                                        Change Password
                                    </Button>
                                </div>
                            </div>

                            <div className="bg-card border border-border rounded-lg p-6">
                                <h2 className="text-lg font-semibold text-foreground mb-4">Two-Factor Authentication</h2>

                                <div className="space-y-4">
                                    <p className="text-sm text-muted-foreground">
                                        {user?.totp_enabled
                                            ? '2FA is enabled on your account'
                                            : '2FA is not enabled. Enable it for additional security.'
                                        }
                                    </p>

                                    {!user?.totp_enabled && (
                                        <p className="text-xs text-muted-foreground">
                                            Contact administrator to enable 2FA
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
