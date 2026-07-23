import { render, fireEvent, waitFor, cleanup } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import LoginPage from './+page.svelte';
import * as api from '$lib/api';

vi.mock('$lib/api', () => ({
	loginUser: vi.fn(),
	getProfile: vi.fn(),
	API_URL: 'http://test'
}));

vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('svelte-i18n', () => ({
	_: {
		subscribe: (fn: (val: (key: string, opts?: any) => string) => void) => {
			fn((key: string, opts?: any) => opts?.default || key);
			return () => {};
		}
	}
}));

describe('Login +page.svelte', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		cleanup();
	});

	it('renders login form with email and password fields', () => {
		const { getByLabelText, getByRole } = render(LoginPage);

		expect(getByLabelText(/email address/i)).toBeInTheDocument();
		expect(getByLabelText(/password/i)).toBeInTheDocument();
		expect(getByRole('button', { name: /login/i })).toBeInTheDocument();
	});

	it('submits login details and authenticates user', async () => {
		const mockToken = 'mock-access-token';
		const mockUser = { id: 1, email: 'user@example.com' };

		vi.mocked(api.loginUser).mockResolvedValue({ access_token: mockToken, token_type: 'bearer' });
		vi.mocked(api.getProfile).mockResolvedValue(mockUser);

		const { getByLabelText, getByRole } = render(LoginPage);

		const emailInput = getByLabelText(/email address/i);
		const passwordInput = getByLabelText(/password/i);
		const submitButton = getByRole('button', { name: /login/i });

		await fireEvent.input(emailInput, { target: { value: 'user@example.com' } });
		await fireEvent.input(passwordInput, { target: { value: 'secret123' } });
		await fireEvent.click(submitButton);

		await waitFor(() => {
			expect(api.loginUser).toHaveBeenCalled();
			expect(api.getProfile).toHaveBeenCalledWith(mockToken);
		});
	});
});
