<script lang="ts">
	import { loginUser, getProfile, API_URL } from '$lib/api';
	import { auth } from '../../stores/auth';
	import { goto } from '$app/navigation';
	import { _ } from 'svelte-i18n';

	let email = '';
	let password = '';
	let error = '';
	let isLoading = false;
	let showPassword = false;

	async function handleSubmit() {
		isLoading = true;
		error = '';

		try {
			const formData = new FormData();
			formData.append('username', email); // OAuth2 expects 'username' field
			formData.append('password', password);

			const data = await loginUser(formData);

			// Fetch complete user profile to get is_superuser and other fields
			const profileResponse = await fetch(`${API_URL}/api/users/me`, {
				headers: {
					Authorization: `Bearer ${data.access_token}`
				}
			});

			if (!profileResponse.ok) {
				throw new Error('Failed to fetch user profile');
			}

			const user = await profileResponse.json();
			auth.login(data.access_token, user);

			// Redirect to home
			goto('/');
		} catch (e: any) {
			error = e.message || 'Login failed';
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="max-w-md mx-auto mt-20 p-10 card">
	<div class="text-center mb-8">
		<h1 class="text-3xl font-bold text-[#0F172A] mb-2">
			{$_('login.welcome_back', { default: 'Welcome Back' })}
		</h1>
		<p class="text-[#334155] text-sm">
			{$_('login.subtitle', { default: 'Log in to manage your job applications' })}
		</p>
	</div>

	{#if error}
		<div
			class="mb-6 p-4 bg-red-50 border border-red-100 text-red-700 rounded-md text-sm flex items-start gap-3"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-5 w-5 text-red-500 shrink-0"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
				/>
			</svg>
			<span>{error}</span>
		</div>
	{/if}

	<form on:submit|preventDefault={handleSubmit} class="space-y-5">
		<div>
			<label for="email" class="block text-sm font-semibold text-[#334155] mb-2"
				>{$_('login.email_address', { default: 'Email Address' })}</label
			>
			<input
				id="email"
				type="email"
				bind:value={email}
				required
				class="input"
				placeholder="you@example.com"
			/>
		</div>

		<div>
			<label for="password" class="block text-sm font-semibold text-[#334155] mb-2"
				>{$_('login.password', { default: 'Password' })}</label
			>
			<div class="relative">
				<input
					id="password"
					type={showPassword ? 'text' : 'password'}
					value={password}
					on:input={(e) => (password = e.currentTarget.value)}
					required
					class="input"
					placeholder="••••••••"
				/>
				<button
					type="button"
					on:click={() => (showPassword = !showPassword)}
					class="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-gray-500 hover:text-[#0369A1] focus:outline-none transition-colors"
					title={showPassword ? 'Hide password' : 'Show password'}
				>
					{#if showPassword}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.046m4.51 4.51l-4.51-4.51M17.25 10.5a7.5 7.5 0 00-6.75-4.5M12 3c4.478 0 8.268 2.943 9.543 7a9.97 9.97 0 01-1.563 3.046m-4.51-4.51l4.51 4.51M9 12a3 3 0 116 0 3 3 0 01-6 0zm-3 0h.01M21 12h.01"
							/>
						</svg>
					{:else}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
							/>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
							/>
						</svg>
					{/if}
				</button>
			</div>
		</div>

		<button type="submit" disabled={isLoading} class="w-full btn btn-primary mt-4">
			{#if isLoading}
				<div class="flex items-center justify-center gap-2">
					<svg
						class="animate-spin h-5 w-5 text-white"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
					>
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					{$_('login.logging_in', { default: 'Logging in...' })}
				</div>
			{:else}
				{$_('login.login_btn', { default: 'Login' })}
			{/if}
		</button>
	</form>

	<div class="mt-8 pt-6 border-t border-[#E2E8F0] text-center text-sm text-[#334155]">
		{$_('login.no_account', { default: "Don't have an account?" })}
		<a href="/register" class="text-[#0369A1] font-semibold hover:underline px-1"
			>{$_('login.create_account', { default: 'Create an account' })}</a
		>
	</div>
</div>
