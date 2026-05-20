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
			// We still keep token in memory for current session state,
			// but we stop putting it in localStorage.
			set({ user, token, isAuthenticated: true });
		},
		logout: async () => {
			// Call backend logout to clear cookie
			try {
				const apiUrl = import.meta.env.VITE_API_URL || '';
				await fetch(`${apiUrl}/api/auth/logout`, {
					method: 'POST',
					credentials: 'include'
				});
			} catch (e) {
				console.error('Logout error:', e);
			}
			set(initialState);
		},
		initialize: async () => {
			if (browser) {
				// We no longer check localStorage for token.
				// We just try to fetch /me. If cookie is present, it will succeed.
				try {
					const apiUrl = import.meta.env.VITE_API_URL || '';
					const response = await fetch(`${apiUrl}/api/users/me`, {
						credentials: 'include'
					});

					if (response.ok) {
						const user = await response.json();
						// Note: token is null here in memory because it's in a cookie,
						// but isAuthenticated is true.
						set({ user, token: null, isAuthenticated: true });
					} else {
						set(initialState);
					}
				} catch (error) {
					set(initialState);
				}
			}
		},
		updateUser: (user: User) => {
			update((state) => ({ ...state, user }));
		}
	};
};

export const auth = createAuthStore();
