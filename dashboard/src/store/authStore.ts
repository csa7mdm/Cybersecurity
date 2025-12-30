import { create } from 'zustand';
import { apiService } from '../services/api';
import { wsService } from '../services/websocket';

interface User {
    id: string;
    email: string;
    username: string;
    role: string;
    features: string[];
    organization_id: string;
}

interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;

    login: (email: string, password: string) => Promise<void>;
    register: (email: string, username: string, password: string, fullName?: string) => Promise<void>;
    logout: () => Promise<void>;
    clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    token: localStorage.getItem('auth_token'),
    isAuthenticated: !!localStorage.getItem('auth_token'),
    isLoading: false,
    error: null,

    login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });

        try {
            const response = await apiService.login(email, password);

            set({
                user: response.user,
                token: response.access_token,
                isAuthenticated: true,
                isLoading: false,
            });

            // Connect to WebSocket
            wsService.connect(response.access_token);
        } catch (error: any) {
            set({
                error: error.response?.data?.error || 'Login failed',
                isLoading: false,
            });
            throw error;
        }
    },

    register: async (email: string, username: string, password: string, fullName?: string) => {
        set({ isLoading: true, error: null });

        try {
            await apiService.register(email, username, password, fullName);
            set({ isLoading: false });
        } catch (error: any) {
            set({
                error: error.response?.data?.error || 'Registration failed',
                isLoading: false,
            });
            throw error;
        }
    },

    logout: async () => {
        set({ isLoading: true });

        try {
            await apiService.logout();
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            wsService.disconnect();
            set({
                user: null,
                token: null,
                isAuthenticated: false,
                isLoading: false,
                error: null,
            });
        }
    },

    clearError: () => set({ error: null }),
}));
