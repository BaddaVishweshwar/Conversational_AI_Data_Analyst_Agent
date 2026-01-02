import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { BarChart3 } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const login = useAuthStore((state) => state.login);
    const googleLogin = useAuthStore((state) => state.googleLogin);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await login(email, password);
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Login failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSuccess = async (credentialResponse: any) => {
        setLoading(true);
        try {
            await googleLogin(credentialResponse.credential);
            navigate('/dashboard');
        } catch (err: any) {
            console.error("Google Login Error:", err);
            setError(err.message || "Google authentication failed. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden p-4">
            {/* Background Blobs */}
            <div className="absolute top-[-10%] right-[-5%] w-[400px] h-[400px] bg-primary/20 rounded-full blur-[100px] -z-10 animate-blob" />
            <div className="absolute bottom-[-10%] left-[-5%] w-[400px] h-[400px] bg-indigo-500/20 rounded-full blur-[100px] -z-10 animate-blob animation-delay-2000" />

            <Card className="w-full max-w-md border-white/20 bg-background/60 backdrop-blur-xl shadow-2xl">
                <CardHeader className="space-y-1 flex flex-col items-center pb-8">
                    <Link to="/" className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-primary/30">
                        <BarChart3 className="w-6 h-6 text-primary-foreground" />
                    </Link>
                    <CardTitle className="text-3xl font-bold font-heading">Welcome Back</CardTitle>
                    <CardDescription className="text-muted-foreground/80 text-center">
                        Enter your credentials to access your dashboard
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
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
                            <div className="flex justify-between items-center ml-1">
                                <label htmlFor="password" className="text-sm font-medium">
                                    Password
                                </label>
                                <a href="#" className="text-xs text-primary hover:underline">Forgot?</a>
                            </div>
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

                        <Button type="submit" className="w-full h-11 rounded-lg font-bold shadow-lg shadow-primary/20 active:scale-95 transition-transform" disabled={loading}>
                            {loading ? 'Authenticating...' : 'Sign In'}
                        </Button>
                    </form>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t border-muted" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-background/0 px-2 text-muted-foreground backdrop-blur-sm">Or continue with</span>
                        </div>
                    </div>

                    <div className="flex justify-center w-full">
                        <div className="w-full flex justify-center">
                            <GoogleLogin
                                onSuccess={handleGoogleSuccess}
                                onError={() => setError("Google login failed")}
                                useOneTap={false} // Disabled OneTap to prevent popup blocks
                                theme="outline"
                                shape="rectangular" // Fixed 'rect' to 'rectangular' to match type definition
                                size="large"
                                width="300"
                            />
                        </div>
                    </div>

                    <p className="text-center text-sm text-muted-foreground">
                        New here?{' '}
                        <Link to="/register" className="text-primary font-bold hover:underline">
                            Create an account
                        </Link>
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
