import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminAPI } from '../lib/adminAPI';
import { useAuthStore } from '../store/authStore';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useToast } from '../hooks/use-toast';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Shield,
    Users,
    UserPlus,
    UserMinus,
    History,
    Search,
    ChevronLeft,
    ChevronRight,
    AlertCircle,
    CheckCircle,
    Trash2,
    Lock,
    Loader2,
} from 'lucide-react';
import TwoFactorSetup from '../components/TwoFactorSetup';

interface User {
    id: number;
    email: string;
    username: string;
    is_admin: boolean;
    is_super_admin: boolean;
    totp_enabled: boolean;
    created_at: string;
}

interface AuditLog {
    id: number;
    admin_user_id: number;
    action: string;
    target_user_id: number | null;
    details: any;
    ip_address: string;
    created_at: string;
}

export default function AdminPage() {
    const { toast } = useToast();
    const navigate = useNavigate();
    const currentUser = useAuthStore((state) => state.user);
    const [users, setUsers] = useState<User[]>([]);
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState<'users' | 'logs' | '2fa'>('users');

    // Strict Access State
    const [isSessionVerified, setIsSessionVerified] = useState(false);
    const [verificationToken, setVerificationToken] = useState('');
    const [verifying, setVerifying] = useState(false);
    const [totalUsers, setTotalUsers] = useState(0);
    const [totalLogs, setTotalLogs] = useState(0);

    // Modal State
    const [showGrantModal, setShowGrantModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [selectedUser, setSelectedUser] = useState<User | null>(null);
    const [modalPassword, setModalPassword] = useState('');
    const [modalToken, setModalToken] = useState('');
    const [modalLoading, setModalLoading] = useState(false);

    // Pagination State
    const [page, setPage] = useState(1);
    const ITEMS_PER_PAGE = 10;

    // Reset page when search or tab changes
    useEffect(() => {
        setPage(1);
    }, [searchQuery, activeTab]);

    useEffect(() => {
        // Only load data if verified or if user needs setup
        if (isSessionVerified) {
            const timer = setTimeout(() => {
                loadData();
            }, 300); // 300ms debounce
            return () => clearTimeout(timer);
        }
    }, [isSessionVerified, page, activeTab, searchQuery]);



    const confirmDeleteUser = async () => {
        if (!selectedUser) return;

        // Optimistic Update: Remove user immediately from UI
        const previousUsers = [...users];
        setUsers(users.filter(u => u.id !== selectedUser.id));
        setShowDeleteModal(false);

        const userIdToDelete = selectedUser.id;
        setSelectedUser(null);

        try {
            await adminAPI.deleteUser(userIdToDelete);
            toast({
                title: 'Success',
                description: 'User deleted successfully',
            });
            // Quietly reload logs
            const logsRes = await adminAPI.getAuditLogs();
            setAuditLogs(logsRes.data);
        } catch (error: any) {
            // Revert if failed
            setUsers(previousUsers);
            toast({
                title: 'Error',
                description: error.response?.data?.detail || 'Failed to delete user',
                variant: 'destructive',
            });
        }
    };

    const handleDeleteClick = (user: User) => {
        setSelectedUser(user);
        setShowDeleteModal(true);
    };

    // ... (handleGrantAdmin, handleRevokeAdmin kept as is)

    // ... (filteredUsers kept as is)

    // In render:
    // ...
    // Button onClick changed to handleDeleteClick(user)

    // Add Delete Modal JSX at the end


    const handleVerifySession = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        setVerifying(true);
        try {
            await adminAPI.verifyTotp(verificationToken);
            setIsSessionVerified(true);
            toast({
                title: 'Access Granted',
                description: 'Admin session verified',
            });
        } catch (error: any) {
            toast({
                title: 'Access Denied',
                description: 'Invalid 2FA code',
                variant: 'destructive',
            });
        } finally {
            setVerifying(false);
        }
    };

    const loadData = async () => {
        setLoading(true);
        try {
            const skip = (page - 1) * ITEMS_PER_PAGE;

            if (activeTab === 'users') {
                // Fetch users
                const res = await adminAPI.listUsers(skip, ITEMS_PER_PAGE, searchQuery);
                setUsers(res.data.items);
                setTotalUsers(res.data.total);
            } else if (activeTab === 'logs') {
                // Fetch logs
                const res = await adminAPI.getAuditLogs(skip, ITEMS_PER_PAGE, searchQuery);
                setAuditLogs(res.data.items);
                setTotalLogs(res.data.total);
            }
        } catch (error: any) {
            toast({
                title: 'Error',
                description: error.response?.data?.detail || 'Failed to load data',
                variant: 'destructive',
            });
        } finally {
            setLoading(false);
        }
    };



    const handleGrantAdmin = async () => {
        if (!selectedUser || !modalPassword || !modalToken) {
            return;
        }

        setModalLoading(true);
        try {
            await adminAPI.grantAdmin(
                selectedUser.id,
                selectedUser.email,
                modalPassword,
                modalToken
            );
            toast({
                title: 'Success',
                description: `Admin access granted to ${selectedUser.email}`,
            });
            setShowGrantModal(false);
            setModalPassword('');
            setModalToken('');
            setSelectedUser(null);
            loadData();
        } catch (error: any) {
            toast({
                title: 'Error',
                description: error.response?.data?.detail || 'Failed to grant admin access',
                variant: 'destructive',
            });
        } finally {
            setModalLoading(false);
        }
    };

    const handleRevokeAdmin = async (user: User) => {
        const password = prompt('Enter your password to confirm:');
        const token = prompt('Enter your 2FA code:');

        if (!password || !token) return;

        try {
            await adminAPI.revokeAdmin(user.id, user.email, password, token);
            toast({
                title: 'Success',
                description: `Admin access revoked from ${user.email}`,
            });
            loadData();
        } catch (error: any) {
            toast({
                title: 'Error',
                description: error.response?.data?.detail || 'Failed to revoke admin access',
                variant: 'destructive',
            });
        }
    };

    // Removed client-side filtering logic
    // Strict Access Control View
    if (!isSessionVerified) {
        // If user doesn't have 2FA enabled, force setup
        if (currentUser?.is_admin && !currentUser?.totp_enabled && !currentUser?.is_super_admin) {
            // Exception: If not enabled, show setup immediately? 
            // Logic: Backend require_2fa blocks API calls if not enabled. 
            // We should probably allow them to see the setup screen.
            // But for now, let's treat "Not Enabled" as "Go to Setup".
            return (
                <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
                    <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 border border-red-100">
                        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <Shield className="w-8 h-8 text-red-600" />
                        </div>
                        <h2 className="text-2xl font-bold text-center mb-2">2FA Setup Required</h2>
                        <p className="text-center text-slate-500 mb-8">
                            You must set up Two-Factor Authentication to access the admin panel.
                        </p>
                        <TwoFactorSetup onComplete={() => window.location.reload()} />
                    </div>
                </div>
            );
        }

        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 border border-slate-100"
                >
                    <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Lock className="w-8 h-8 text-purple-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-center mb-2">Admin Access Verification</h2>
                    <p className="text-center text-slate-500 mb-8">
                        Please enter your 6-digit 2FA code to continue.
                    </p>

                    <form onSubmit={handleVerifySession} className="space-y-6">
                        <div>
                            <Input
                                type="text"
                                maxLength={6}
                                value={verificationToken}
                                onChange={(e) => setVerificationToken(e.target.value.replace(/\D/g, ''))}
                                placeholder="000 000"
                                className="text-center text-2xl tracking-[0.5em] h-14 font-mono"
                                autoFocus
                            />
                        </div>
                        <Button
                            type="submit"
                            className="w-full h-11 text-lg"
                            disabled={verifying || verificationToken.length !== 6}
                        >
                            {verifying ? 'Verifying...' : 'Verify Access'}
                        </Button>
                        <Button
                            variant="ghost"
                            className="w-full"
                            onClick={() => navigate('/dashboard')}
                        >
                            Cancel
                        </Button>
                    </form>
                </motion.div>
            </div>
        );
    }

    // 2. Loading State
    if (loading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-50">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header */}
            <div className="bg-white border-b border-slate-200">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => navigate('/dashboard')}
                            >
                                <ChevronLeft className="w-4 h-4 mr-2" />
                                Back
                            </Button>
                            <div>
                                <h1 className="text-2xl font-bold text-slate-900">Admin Panel</h1>
                                <p className="text-sm text-slate-500">Manage users and system settings</p>
                            </div>
                        </div>
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
                            <Shield className="w-6 h-6 text-white" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="bg-white border-b border-slate-200">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="flex gap-6">
                        {[
                            { id: 'users', label: 'Users', icon: Users },
                            { id: 'logs', label: 'Audit Logs', icon: History },
                            { id: '2fa', label: '2FA Setup', icon: Shield },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${activeTab === tab.id
                                    ? 'border-purple-600 text-purple-600'
                                    : 'border-transparent text-slate-600 hover:text-slate-900'
                                    }`}
                            >
                                <tab.icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-6 py-8">
                <AnimatePresence mode="wait">
                    {activeTab === 'users' && (
                        <motion.div
                            key="users"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                        >
                            {/* Search */}
                            <div className="mb-6">
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <Input
                                        type="text"
                                        placeholder="Search users..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="pl-10"
                                    />
                                </div>
                            </div>

                            {/* Users Table */}
                            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                                <table className="w-full">
                                    <thead className="bg-slate-50 border-b border-slate-200">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                                                User
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                                                Role
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                                                2FA
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                                                Created
                                            </th>
                                            <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase">
                                                Actions
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-200">
                                        {users.map((user) => (
                                            <tr key={user.id} className="hover:bg-slate-50">
                                                <td className="px-6 py-4">
                                                    <div>
                                                        <div className="font-medium text-slate-900">
                                                            {user.username}
                                                        </div>
                                                        <div className="text-sm text-slate-500">{user.email}</div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    {user.is_super_admin ? (
                                                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-700">
                                                            Super Admin
                                                        </span>
                                                    ) : user.is_admin ? (
                                                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
                                                            Admin
                                                        </span>
                                                    ) : (
                                                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-slate-100 text-slate-700">
                                                            User
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4">
                                                    {user.totp_enabled ? (
                                                        <CheckCircle className="w-5 h-5 text-green-600" />
                                                    ) : (
                                                        <AlertCircle className="w-5 h-5 text-slate-300" />
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-slate-500">
                                                    {new Date(user.created_at).toLocaleDateString()}
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <div className="flex justify-end gap-2">
                                                        {currentUser?.is_admin && !user.is_super_admin && (
                                                            <>
                                                                {!user.is_admin ? (
                                                                    <Button
                                                                        size="sm"
                                                                        variant="outline"
                                                                        onClick={() => {
                                                                            setSelectedUser(user);
                                                                            setShowGrantModal(true);
                                                                        }}
                                                                    >
                                                                        <UserPlus className="w-4 h-4 mr-2" />
                                                                        Grant
                                                                    </Button>
                                                                ) : (
                                                                    <Button
                                                                        size="sm"
                                                                        variant="outline"
                                                                        onClick={() => handleRevokeAdmin(user)}
                                                                        className="text-orange-600 hover:text-orange-700 hover:bg-orange-50"
                                                                    >
                                                                        <UserMinus className="w-4 h-4 mr-2" />
                                                                        Revoke
                                                                    </Button>
                                                                )}

                                                                {/* DELETE BUTTON - Visible to all admins for accessibility */}
                                                                <Button
                                                                    size="sm"
                                                                    variant="ghost"
                                                                    onClick={() => handleDeleteClick(user)}
                                                                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                                                >
                                                                    <Trash2 className="w-4 h-4" />
                                                                </Button>
                                                            </>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination Controls (Users) */}
                            {totalUsers > ITEMS_PER_PAGE && (
                                <div className="flex items-center justify-between mt-4">
                                    <div className="text-sm text-slate-500">
                                        Showing {((page - 1) * ITEMS_PER_PAGE) + 1} to {Math.min(page * ITEMS_PER_PAGE, totalUsers)} of {totalUsers} users
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setPage(p => Math.max(1, p - 1))}
                                            disabled={page === 1}
                                        >
                                            <ChevronLeft className="w-4 h-4" />
                                        </Button>
                                        <div className="flex items-center px-4 font-medium text-sm text-slate-600">
                                            Page {page} of {Math.ceil(totalUsers / ITEMS_PER_PAGE)}
                                        </div>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setPage(p => Math.min(Math.ceil(totalUsers / ITEMS_PER_PAGE), p + 1))}
                                            disabled={page >= Math.ceil(totalUsers / ITEMS_PER_PAGE)}
                                        >
                                            <ChevronRight className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {activeTab === 'logs' && (
                        <motion.div
                            key="logs"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                        >
                            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                                <table className="w-full">
                                    <thead className="bg-slate-50 border-b border-slate-200">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                                                Action
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                                                Admin
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                                                IP Address
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">
                                                Time
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-200">
                                        {auditLogs.map((log) => (
                                            <tr key={log.id} className="hover:bg-slate-50">
                                                <td className="px-6 py-4">
                                                    <span className="font-medium text-slate-900">
                                                        {log.action.replace(/_/g, ' ').toUpperCase()}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-sm text-slate-600">
                                                    User #{log.admin_user_id}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-slate-600">
                                                    {log.ip_address}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-slate-500">
                                                    {new Date(log.created_at).toLocaleString()}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination Controls (Logs) */}
                            {totalLogs > ITEMS_PER_PAGE && (
                                <div className="flex items-center justify-between mt-4">
                                    <div className="text-sm text-slate-500">
                                        Showing {((page - 1) * ITEMS_PER_PAGE) + 1} to {Math.min(page * ITEMS_PER_PAGE, totalLogs)} of {totalLogs} logs
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setPage(p => Math.max(1, p - 1))}
                                            disabled={page === 1}
                                        >
                                            <ChevronLeft className="w-4 h-4" />
                                        </Button>
                                        <div className="flex items-center px-4 font-medium text-sm text-slate-600">
                                            Page {page} of {Math.ceil(totalLogs / ITEMS_PER_PAGE)}
                                        </div>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setPage(p => Math.min(Math.ceil(totalLogs / ITEMS_PER_PAGE), p + 1))}
                                            disabled={page >= Math.ceil(totalLogs / ITEMS_PER_PAGE)}
                                        >
                                            <ChevronRight className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {activeTab === '2fa' && (
                        <motion.div
                            key="2fa"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="max-w-2xl mx-auto"
                        >
                            <div className="bg-white rounded-xl border border-slate-200 p-8">
                                <TwoFactorSetup onComplete={loadData} />
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Grant Admin Modal */}
            {showGrantModal && selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-white rounded-xl p-6 max-w-md w-full mx-4"
                    >
                        <h3 className="text-xl font-bold mb-4">Grant Admin Access</h3>
                        <p className="text-slate-600 mb-6">
                            Grant admin access to <strong>{selectedUser.email}</strong>?
                        </p>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">Your Password</label>
                                <Input
                                    type="password"
                                    value={modalPassword}
                                    onChange={(e) => setModalPassword(e.target.value)}
                                    placeholder="Enter your password"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">Your 2FA Code</label>
                                <Input
                                    type="text"
                                    maxLength={6}
                                    value={modalToken}
                                    onChange={(e) => setModalToken(e.target.value.replace(/\D/g, ''))}
                                    placeholder="000000"
                                    className="text-center tracking-widest"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <Button
                                variant="outline"
                                onClick={() => {
                                    setShowGrantModal(false);
                                    setModalPassword('');
                                    setModalToken('');
                                    setSelectedUser(null);
                                }}
                                className="flex-1"
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={handleGrantAdmin}
                                disabled={modalLoading || !modalPassword || modalToken.length !== 6}
                                className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600"
                            >
                                {modalLoading ? 'Granting...' : 'Grant Admin'}
                            </Button>
                        </div>
                    </motion.div>
                </div>
            )}
            {/* Delete Confirmation Modal */}
            {showDeleteModal && selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-white rounded-xl p-6 max-w-md w-full mx-4"
                    >
                        <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4 mx-auto">
                            <Trash2 className="w-6 h-6 text-red-600" />
                        </div>
                        <h3 className="text-xl font-bold mb-2 text-center">Delete User?</h3>
                        <p className="text-slate-600 mb-6 text-center">
                            Are you sure you want to delete <strong>{selectedUser.email}</strong>?
                            <br />
                            <span className="text-red-600 font-medium my-2 block">
                                This action cannot be undone.
                            </span>
                        </p>

                        <div className="flex gap-3">
                            <Button
                                variant="outline"
                                onClick={() => {
                                    setShowDeleteModal(false);
                                    setSelectedUser(null);
                                }}
                                className="flex-1"
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={confirmDeleteUser}
                                className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                            >
                                Delete User
                            </Button>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
}
