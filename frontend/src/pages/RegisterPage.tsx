import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { UserPlus } from 'lucide-react';

export default function RegisterPage() {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const register = useAuthStore((state) => state.register);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        setLoading(true);

        try {
            await register(email, username, password);
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden p-4">
            {/* Background Blobs */}
            <div className="absolute top-[-10%] right-[-5%] w-[400px] h-[400px] bg-primary/20 rounded-full blur-[100px] -z-10 animate-blob" />
            <div className="absolute bottom-[-10%] left-[-5%] w-[400px] h-[400px] bg-indigo-500/20 rounded-full blur-[100px] -z-10 animate-blob animation-delay-4000" />

            <Card className="w-full max-w-md border-white/20 bg-background/60 backdrop-blur-xl shadow-2xl">
                <CardHeader className="space-y-1 flex flex-col items-center pb-8">
                    <Link to="/" className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-primary/30">
                        <UserPlus className="w-6 h-6 text-primary-foreground" />
                    </Link>
                    <CardTitle className="text-3xl font-bold font-heading">Create Account</CardTitle>
                    <CardDescription className="text-muted-foreground/80 text-center">
                        Join 2,000+ companies using AI to analyze data
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-lg border border-destructive/20">
                                {error}
                            </div>
                        )}

                        <div className="space-y-2">
                            <label htmlFor="email" className="text-sm font-medium ml-1">
                                Email Address
                            </label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="name@company.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="h-11 rounded-lg bg-background/50 border-white/10"
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="username" className="text-sm font-medium ml-1">
                                Full Name
                            </label>
                            <Input
                                id="username"
                                type="text"
                                placeholder="John Doe"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="h-11 rounded-lg bg-background/50 border-white/10"
                                required
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label htmlFor="password" className="text-sm font-medium ml-1">
                                    Password
                                </label>
                                <Input
                                    id="password"
                                    type="password"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="h-11 rounded-lg bg-background/50 border-white/10"
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label htmlFor="confirmPassword" className="text-sm font-medium ml-1">
                                    Confirm
                                </label>
                                <Input
                                    id="confirmPassword"
                                    type="password"
                                    placeholder="••••••••"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="h-11 rounded-lg bg-background/50 border-white/10"
                                    required
                                />
                            </div>
                        </div>

                        <Button type="submit" className="w-full h-12 rounded-lg font-bold shadow-lg shadow-primary/20 mt-2 active:scale-95 transition-transform" disabled={loading}>
                            {loading ? 'Creating Account...' : 'Get Started Free'}
                        </Button>

                        <p className="text-center text-sm text-muted-foreground pt-4">
                            Already have an account?{' '}
                            <Link to="/login" className="text-primary font-bold hover:underline">
                                Sign in
                            </Link>
                        </p>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
