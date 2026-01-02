import { create } from 'zustand';
import { authAPI } from '../lib/api';

interface User {
    id: number;
    email: string;
    username: string;
    is_active: boolean;
    is_admin?: boolean;
    is_super_admin?: boolean;
    totp_enabled?: boolean;
}

interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    googleLogin: (idToken: string) => Promise<void>;
    register: (email: string, username: string, password: string) => Promise<void>;
    logout: () => void;
    checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    isAuthenticated: false,
    isLoading: true,

    login: async (email: string, password: string) => {
        const response = await authAPI.login({ email, password });
        const { access_token, refresh_token } = response.data;

        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        const userResponse = await authAPI.getMe();
        set({ user: userResponse.data, isAuthenticated: true });
    },

    googleLogin: async (idToken: string) => {
        // We'll need to add this to authAPI in lib/api.ts as well
        const response = await (authAPI as any).googleLogin({ id_token: idToken });
        const { access_token, refresh_token } = response.data;

        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        const userResponse = await authAPI.getMe();
        set({ user: userResponse.data, isAuthenticated: true });
    },

    register: async (email: string, username: string, password: string) => {
        const response = await authAPI.register({ email, username, password });
        const { access_token, refresh_token } = response.data;

        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        const userResponse = await authAPI.getMe();
        set({ user: userResponse.data, isAuthenticated: true });
    },

    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, isAuthenticated: false });
    },

    checkAuth: async () => {
        const token = localStorage.getItem('access_token');

        if (!token) {
            set({ isLoading: false, isAuthenticated: false });
            return;
        }

        try {
            const response = await authAPI.getMe();
            set({ user: response.data, isAuthenticated: true, isLoading: false });
        } catch (error) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            set({ user: null, isAuthenticated: false, isLoading: false });
        }
    },
}));
