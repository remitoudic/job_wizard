import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export interface User {
    id?: number;
    email: string;
    username?: string;
    first_name?: string;
    surname?: string;
    job_title?: string;
    linkedin_url?: string;
    portfolio_url?: string;
    website_url?: string;
    profile_picture_url?: string;

    street?: string;
    city?: string;
    postcode?: string;
    country?: string;

    phone?: string;
    is_superuser?: boolean;
    last_login?: string;
}

interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
}

const initialState: AuthState = {
    user: null,
    token: null,
    isAuthenticated: false
};

const createAuthStore = () => {
    const { subscribe, set, update } = writable<AuthState>(initialState);

    return {
        subscribe,
        login: (token: string, user: User) => {
            if (browser) {
                localStorage.setItem('token', token);
            }
            set({ user, token, isAuthenticated: true });
        },
        logout: () => {
            if (browser) {
                localStorage.removeItem('token');
            }
            set(initialState);
        },
        initialize: async () => {
            if (browser) {
                const token = localStorage.getItem('token');
                if (token) {
                    try {
                        // Use configured API URL or fallback to relative path for production
                        const apiUrl = import.meta.env.VITE_API_URL || '';

                        // Fetch user profile to get full user data including is_superuser
                        const response = await fetch(`${apiUrl}/api/users/me`, {
                            headers: {
                                Authorization: `Bearer ${token}`
                            }
                        });

                        if (response.ok) {
                            const user = await response.json();
                            set({ user, token, isAuthenticated: true });
                        } else {
                            // Token is invalid, clear it
                            localStorage.removeItem('token');
                            set(initialState);
                        }
                    } catch (error) {
                        console.error('Failed to fetch user profile:', error);
                        set(initialState);
                    }
                }
            }
        },
        updateUser: (user: User) => {
            update(state => ({ ...state, user }));
        }
    };
};

export const auth = createAuthStore();
