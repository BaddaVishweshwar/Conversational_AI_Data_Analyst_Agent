import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Database, Mail, Lock, User as UserIcon } from 'lucide-react';
import { api } from '../lib/api';

export default function RegisterPage() {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await api.post('/auth/register', {
                email,
                username,
                password
            });

            // Save tokens
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('refresh_token', response.data.refresh_token);

            // Navigate to analytics
            navigate('/chat');
            window.location.reload(); // Force reload to update auth state
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
            {/* Subtle background effect */}
            <div className="absolute inset-0 opacity-5">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent rounded-full blur-3xl" />
            </div>

            {/* Register Card */}
            <div className="relative w-full max-w-md px-6">
                {/* Logo */}
                <div className="flex items-center justify-center gap-2 mb-12">
                    <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
                        <Database className="w-6 h-6 text-accent" />
                    </div>
                    <span className="text-xl font-semibold text-foreground">AI Data Analyst</span>
                </div>

                {/* Card */}
                <div className="bg-card border border-border rounded-2xl p-8 shadow-depth">
                    <div className="mb-8 text-center">
                        <h1 className="text-2xl font-semibold mb-2 text-foreground">Create your account</h1>
                        <p className="text-sm text-muted-foreground">
                            Get started with intelligent data analysis
                        </p>
                    </div>

                    {error && (
                        <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-sm text-destructive">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="text-sm font-medium text-foreground mb-1.5 block">
                                Email
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                <Input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="you@company.com"
                                    required
                                    className="pl-10 h-11 bg-muted border-border focus:border-accent"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="text-sm font-medium text-foreground mb-1.5 block">
                                Username
                            </label>
                            <div className="relative">
                                <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                <Input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    placeholder="username"
                                    required
                                    className="pl-10 h-11 bg-muted border-border focus:border-accent"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="text-sm font-medium text-foreground mb-1.5 block">
                                Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                <Input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    minLength={6}
                                    className="pl-10 h-11 bg-muted border-border focus:border-accent"
                                />
                            </div>
                        </div>

                        <Button
                            type="submit"
                            className="w-full h-11 bg-accent hover:bg-accent/90 text-white font-medium"
                            disabled={loading}
                        >
                            {loading ? 'Creating account...' : 'Sign up'}
                        </Button>
                    </form>

                    <p className="text-center text-sm text-muted-foreground mt-6">
                        Already have an account?{' '}
                        <Link to="/login" className="text-accent hover:underline font-medium">
                            Sign in
                        </Link>
                    </p>
                </div>

                {/* Privacy Note */}
                <p className="text-center text-xs text-muted-foreground mt-6">
                    Your data stays private. No training on your data.
                </p>
            </div>
        </div>
    );
}
