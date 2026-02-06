<script lang="ts">
	import "../app.css";
	import { onMount } from "svelte";
	import { auth } from "../stores/auth";
	import { goto } from "$app/navigation";
	import { page } from "$app/stores";
	import Sidebar from "$lib/components/Sidebar.svelte";

	export let data: any = {};
	export let params: Record<string, string> = {};

	onMount(() => {
		auth.initialize();
	});

	function handleLogout() {
		auth.logout();
		goto("/login");
	}
</script>

<!-- Sidebar for authenticated users -->
{#if $auth.isAuthenticated}
	<Sidebar />
{/if}

<div
	class="min-h-screen bg-[#F8FAFC] flex flex-col font-body {$auth.isAuthenticated
		? 'md:ml-16'
		: ''}"
>
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
						data-sveltekit-reload
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
							class="font-bold text-xl text-[#0F172A] tracking-tight transition-colors group-hover:text-[#0369A1]"
							>Vite a Job</span
						>
					</a>
				</div>

				<!-- Right Side Menu - Empty for authenticated users, normal for guests -->
				<div class="flex items-center gap-6">
					{#if !$auth.isAuthenticated}
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
	<main class="flex-grow {$auth.isAuthenticated ? 'mb-16 md:mb-0' : ''}">
		<slot />
	</main>

	<!-- Footer -->
	<footer class="bg-white border-t border-[#E2E8F0] mt-auto">
		<div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
			<div
				class="flex flex-col md:flex-row justify-between items-center gap-4"
			>
				<div class="flex items-center gap-2 grayscale opacity-50">
					<span class="font-bold text-gray-900 tracking-tight"
						>Vite a Job</span
					>
				</div>
				<p class="text-sm text-[#64748B]">
					&copy; 2026 Vite a Job. All rights reserved.
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
