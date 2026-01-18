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

<div class="min-h-screen bg-gray-50 flex flex-col">
	<!-- Navbar -->
	<nav class="bg-white border-b border-gray-200">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-between h-16">
				<!-- Logo / Brand -->
				<div class="flex items-center">
					<a href="/" class="flex-shrink-0 flex items-center gap-2">
						<span class="text-2xl">🧙‍♂️</span>
						<span
							class="font-bold text-xl text-gray-900 tracking-tight"
							>Job Wizard</span
						>
					</a>

					<!-- Desktop Menu -->
					<div class="hidden sm:ml-8 sm:flex sm:space-x-8">
						<a
							href="/"
							class="text-gray-900 inline-flex items-center px-1 pt-1 border-b-2 border-transparent hover:border-primary-500 text-sm font-medium"
						>
							Home
						</a>
					</div>
				</div>

				<!-- Right Side Menu -->
				<div class="flex items-center gap-4">
					{#if $auth.isAuthenticated}
						<div class="flex items-center gap-4">
							{#if $auth.user}
								<span class="text-sm text-gray-600"
									>Hi, <strong>{$auth.user.username}</strong
									></span
								>
							{/if}
							<a
								href="/profile"
								class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 transition-colors"
							>
								Profile
							</a>
							{#if $auth.user?.is_superuser}
								<a
									href="/admin"
									class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
									class:border-indigo-500={$page.url
										.pathname === "/admin"}
									class:text-gray-900={$page.url.pathname ===
										"/admin"}
								>
									Admin
								</a>
							{/if}
							<button
								on:click={handleLogout}
								class="text-red-600 hover:text-red-700 px-3 py-2 rounded-md text-sm font-medium hover:bg-red-50 transition-colors"
							>
								Logout
							</button>
						</div>
					{:else}
						<div class="flex items-center gap-2">
							<a
								href="/login"
								class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 transition-colors"
							>
								Login
							</a>
							<a
								href="/register"
								class="bg-primary-600 text-white hover:bg-primary-700 px-4 py-2 rounded-md text-sm font-medium transition-colors shadow-sm"
							>
								Register
							</a>
						</div>
					{/if}
				</div>
			</div>
		</div>
	</nav>

	<!-- Main Content -->
	<main class="flex-grow">
		<div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
			<slot />
		</div>
	</main>

	<!-- Footer -->
	<footer class="bg-white border-t border-gray-200 mt-auto">
		<div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
			<p class="text-center text-sm text-gray-500">
				&copy; 2026 Job Wizard AI. All rights reserved.
			</p>
		</div>
	</footer>
</div>
