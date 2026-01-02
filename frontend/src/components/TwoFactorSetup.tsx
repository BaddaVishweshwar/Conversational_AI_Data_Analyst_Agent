import { useState } from 'react';
import { adminAPI } from '../lib/adminAPI';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { useToast } from '../hooks/use-toast';
import { motion } from 'framer-motion';
import { Shield, Check, AlertCircle } from 'lucide-react';

interface TwoFactorSetupProps {
    onComplete: () => void;
}

export default function TwoFactorSetup({ onComplete }: TwoFactorSetupProps) {
    const { toast } = useToast();
    const [step, setStep] = useState<'setup' | 'verify'>('setup');
    const [qrCode, setQrCode] = useState<string>('');
    const [secret, setSecret] = useState<string>('');
    const [token, setToken] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSetup = async () => {
        setLoading(true);
        try {
            const response = await adminAPI.setup2FA();
            setQrCode(response.data.qr_code);
            setSecret(response.data.secret);
            setStep('verify');
            toast({
                title: 'QR Code Generated',
                description: 'Scan the QR code with Google Authenticator',
            });
        } catch (error: any) {
            toast({
                title: 'Error',
                description: error.response?.data?.detail || 'Failed to setup 2FA',
                variant: 'destructive',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleVerify = async () => {
        if (!token || token.length !== 6) {
            toast({
                title: 'Invalid Token',
                description: 'Please enter a 6-digit code',
                variant: 'destructive',
            });
            return;
        }

        setLoading(true);
        try {
            await adminAPI.verify2FA(token);
            toast({
                title: '2FA Enabled',
                description: 'Two-factor authentication is now active',
            });
            onComplete();
        } catch (error: any) {
            toast({
                title: 'Verification Failed',
                description: error.response?.data?.detail || 'Invalid 2FA token',
                variant: 'destructive',
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-md mx-auto">
            {step === 'setup' ? (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center"
                >
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center mx-auto mb-6">
                        <Shield className="w-10 h-10 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Enable Two-Factor Authentication</h2>
                    <p className="text-slate-600 mb-8">
                        Secure your admin account with Google Authenticator
                    </p>
                    <Button
                        onClick={handleSetup}
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                    >
                        {loading ? 'Generating...' : 'Generate QR Code'}
                    </Button>
                </motion.div>
            ) : (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-6"
                >
                    <div className="text-center">
                        <h2 className="text-2xl font-bold mb-2">Scan QR Code</h2>
                        <p className="text-slate-600">
                            Use Google Authenticator to scan this code
                        </p>
                    </div>

                    {/* QR Code */}
                    <div className="bg-card p-6 rounded-xl border-2 border-border">
                        <img src={qrCode} alt="QR Code" className="w-full" />
                    </div>

                    {/* Manual Entry */}
                    <div className="bg-muted p-4 rounded-lg">
                        <p className="text-sm text-slate-600 mb-2">Or enter manually:</p>
                        <code className="text-sm font-mono bg-card px-3 py-2 rounded border border-border block">
                            {secret}
                        </code>
                    </div>

                    {/* Verification */}
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Enter 6-digit code
                            </label>
                            <Input
                                type="text"
                                maxLength={6}
                                value={token}
                                onChange={(e) => setToken(e.target.value.replace(/\D/g, ''))}
                                placeholder="000000"
                                className="text-center text-2xl tracking-widest"
                            />
                        </div>
                        <Button
                            onClick={handleVerify}
                            disabled={loading || token.length !== 6}
                            className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                        >
                            {loading ? 'Verifying...' : 'Verify & Enable 2FA'}
                        </Button>
                    </div>
                </motion.div>
            )}
        </div>
    );
}
