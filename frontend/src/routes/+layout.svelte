<script lang="ts">
	import "../app.css";
	import { onMount } from "svelte";
	import { auth } from "../stores/auth";
	import { goto } from "$app/navigation";
	import { page } from "$app/stores";

	onMount(() => {
		auth.initialize();
	});

	function handleLogout() {
		auth.logout();
		goto("/login");
	}
</script>

<div class="min-h-screen bg-[#F8FAFC] flex flex-col font-body">
	<!-- Navbar -->
	<nav
		class="bg-white/80 backdrop-blur-md border-b border-[#E2E8F0] sticky top-0 z-50"
	>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-between h-16">
				<!-- Logo / Brand -->
				<div class="flex items-center">
					<a
						href="/"
						class="flex-shrink-0 flex items-center gap-3 group"
					>
						<div
							class="p-1.5 bg-[#0F172A] rounded-md transition-transform group-hover:scale-110"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-6 w-6 text-white"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M13 10V3L4 14h7v7l9-11h-7z"
								/>
							</svg>
						</div>
						<span
							class="font-bold text-xl text-[#0F172A] tracking-tight"
							>Job Wizard</span
						>
					</a>
				</div>

				<!-- Right Side Menu -->
				<div class="flex items-center gap-6">
					{#if $auth.isAuthenticated}
						<div class="flex items-center gap-6">
							<a
								href="/"
								class="text-sm font-semibold transition-all {$page
									.url.pathname === '/'
									? 'text-[#0369A1]'
									: 'text-[#64748B] hover:text-[#0F172A]'}"
							>
								Home
							</a>
							<a
								href="/profile"
								class="text-sm font-semibold transition-all {$page
									.url.pathname === '/profile'
									? 'text-[#0369A1]'
									: 'text-[#64748B] hover:text-[#0F172A]'}"
							>
								Profile
							</a>
							{#if $auth.user?.is_superuser}
								<a
									href="/admin"
									class="text-sm font-semibold transition-all {$page
										.url.pathname === '/admin'
										? 'text-[#0369A1]'
										: 'text-[#64748B] hover:text-[#0F172A]'}"
								>
									Admin
								</a>
							{/if}
							<div class="h-4 w-[1px] bg-[#E2E8F0]"></div>
							<button
								on:click={handleLogout}
								class="text-sm font-semibold text-red-500 hover:text-red-600 transition-colors"
							>
								Logout
							</button>
						</div>
					{:else}
						<div class="flex items-center gap-4">
							<a
								href="/login"
								class="text-sm font-semibold text-[#64748B] hover:text-[#0F172A] transition-colors"
							>
								Login
							</a>
							<a
								href="/register"
								class="btn btn-primary text-sm py-2 px-5"
							>
								Get Started
							</a>
						</div>
					{/if}
				</div>
			</div>
		</div>
	</nav>

	<!-- Main Content -->
	<main class="flex-grow">
		<slot />
	</main>

	<!-- Footer -->
	<footer class="bg-white border-t border-[#E2E8F0] mt-auto">
		<div class="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
			<div
				class="flex flex-col md:flex-row justify-between items-center gap-6"
			>
				<div class="flex items-center gap-2 grayscale opacity-50">
					<span class="text-xl">🧙‍♂️</span>
					<span class="font-bold text-gray-900 tracking-tight"
						>Job Wizard</span
					>
				</div>
				<p class="text-sm text-[#64748B]">
					&copy; 2026 Job Wizard AI. All rights reserved.
				</p>
				<div class="flex gap-6">
					<a
						href="#"
						class="text-xs font-semibold text-[#64748B] hover:text-[#0F172A]"
						>Privacy</a
					>
					<a
						href="#"
						class="text-xs font-semibold text-[#64748B] hover:text-[#0F172A]"
						>Terms</a
					>
				</div>
			</div>
		</div>
	</footer>
</div>
