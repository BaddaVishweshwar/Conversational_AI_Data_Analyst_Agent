import { api } from './api';

// Admin API client
export const adminAPI = {
    // 2FA Setup
    setup2FA: () => api.post('/admin/setup-2fa'),
    verify2FA: (token: string) => api.post('/admin/verify-2fa', { token }),

    // Admin Login
    login: (email: string, password: string, totp_token: string) =>
        api.post('/admin/login', { email, password, totp_token }),

    // User Management
    listUsers: (skip = 0, limit = 10, search = '') => api.get('/admin/users', { params: { skip, limit, search } }),
    grantAdmin: (user_id: number, email: string, password: string, totp_token: string) =>
        api.post('/admin/grant-admin', { user_id, email, password, totp_token }),
    revokeAdmin: (user_id: number, email: string, password: string, totp_token: string) =>
        api.post('/admin/revoke-admin', { user_id, email, password, totp_token }),

    // Audit Logs
    // Audit Logs
    getAuditLogs: (skip = 0, limit = 10, search = '') => api.get('/admin/audit-logs', { params: { skip, limit, search } }),

    // New methods
    deleteUser: (userId: number) => api.delete(`/admin/users/${userId}`),
    verifyTotp: (token: string) => api.post('/admin/verify-totp', { token }),
};
