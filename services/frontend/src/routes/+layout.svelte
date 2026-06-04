<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { auth } from '../stores/auth';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import '$lib/i18n';
	import { isLoading, locale, _ } from 'svelte-i18n';
	onMount(() => {
		auth.initialize();
	});

	$: {
		if ($auth.user?.preferred_language) {
			locale.set($auth.user.preferred_language);
		}
	}

	function handleLogout() {
		auth.logout();
		goto('/login');
	}
</script>

{#if !$isLoading}
	{#if $auth.isAuthenticated}
		<Sidebar />
	{/if}

	<SEO />

	<div
		class="min-h-screen bg-[#F8FAFC] flex flex-col font-body {$auth.isAuthenticated
			? 'md:ml-16'
			: ''}"
	>
		{#if !$auth.isAuthenticated}
			<nav class="bg-white/80 backdrop-blur-md border-b border-[#E2E8F0] sticky top-0 z-50">
				<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<div class="flex justify-between h-16">
						<div class="flex items-center" />

						<div class="flex items-center gap-6">
							<div class="flex items-center gap-4">
								<a
									href="/login"
									class="text-sm font-semibold text-[#64748B] hover:text-[#0F172A] transition-colors"
								>
									{$_('register.sign_in', { default: 'Sign in' })}
								</a>
								<a href="/register" class="btn btn-primary text-sm py-2 px-5">
									{$_('main.get_started', { default: 'Get Started' })}
								</a>
							</div>
						</div>
					</div>
				</div>
			</nav>
		{/if}

		<main class="flex-grow {$auth.isAuthenticated ? 'mb-16 md:mb-0' : ''}">
			<slot />
		</main>

		<footer class="bg-white border-t border-[#E2E8F0] mt-auto">
			<div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
				<div class="flex flex-col md:flex-row justify-between items-center gap-4">
					<div class="flex items-center gap-2 grayscale opacity-50">
						<span class="font-bold text-gray-900 tracking-tight">Vite a Job</span>
					</div>
					<p class="text-sm text-[#64748B]">&copy; 2026 Vite a Job. All rights reserved.</p>
					<div class="flex gap-6">
						<a href="/privacy" class="text-xs font-semibold text-[#64748B] hover:text-[#0F172A]"
							>Privacy</a
						>
						<a href="/terms" class="text-xs font-semibold text-[#64748B] hover:text-[#0F172A]"
							>Terms</a
						>
					</div>
				</div>
			</div>
		</footer>
	</div>
{/if}
