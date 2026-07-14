<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '../../stores/auth';
	import { getUsers, createUser, getDebugHealth, type User } from '$lib/api';

	let users: User[] = [];
	let error = '';
	let isLoading = true;

	// Tab navigation state
	let activeTab: 'users' | 'health' = 'users';

	// Health diagnostics state
	let healthData: any = null;
	let isHealthLoading = false;
	let healthError = '';
	let healthLatencyMs = 0;

	// Modal & creation form state
	let isNewUserModalOpen = false;
	let isSubmittingUser = false;
	let userFormError = '';
	let userFormSuccess = '';

	// Form fields
	let firstName = '';
	let surname = '';
	let email = '';
	let username = '';
	let password = '';
	let isSuperuser = false;

	// Timer handle for modal auto-close — cleaned up on component destroy
	let modalCloseTimer: ReturnType<typeof setTimeout> | null = null;
	onDestroy(() => {
		if (modalCloseTimer) clearTimeout(modalCloseTimer);
	});

	onMount(async () => {
		// Wait a bit for auth.initialize() to complete
		await new Promise((resolve) => setTimeout(resolve, 500));

		if (!$auth.isAuthenticated || !$auth.user?.is_superuser) {
			goto('/');
			return;
		}

		try {
			users = await getUsers();
		} catch (e) {
			error = 'Failed to load users';
			console.error(e);
		} finally {
			isLoading = false;
		}
	});

	async function loadHealth() {
		isHealthLoading = true;
		healthError = '';
		const startTime = performance.now();
		try {
			healthData = await getDebugHealth();
			healthLatencyMs = Math.round(performance.now() - startTime);
		} catch (e: any) {
			healthError = e.message || 'Failed to fetch system health status';
			console.error(e);
		} finally {
			isHealthLoading = false;
		}
	}

	function switchTab(tab: 'users' | 'health') {
		activeTab = tab;
		// Always refresh health data when switching to the health tab
		if (tab === 'health') {
			loadHealth();
		}
	}

	async function handleCreateUser() {
		isSubmittingUser = true;
		userFormError = '';
		userFormSuccess = '';

		const payload = {
			email,
			username: username || undefined,
			first_name: firstName || undefined,
			surname: surname || undefined,
			password,
			is_superuser: isSuperuser
		};

		try {
			await createUser(payload);
			userFormSuccess = 'User created successfully!';
			// Refresh the user list
			users = await getUsers();

			// Clear fields
			firstName = '';
			surname = '';
			email = '';
			username = '';
			password = '';
			isSuperuser = false;

			// Close modal after brief success presentation
			modalCloseTimer = setTimeout(() => {
				isNewUserModalOpen = false;
				userFormSuccess = '';
			}, 1200);
		} catch (e: any) {
			userFormError = e.message || 'Failed to create new user';
		} finally {
			isSubmittingUser = false;
		}
	}

	function formatDate(dateString?: string) {
		if (!dateString) return 'Never';
		return new Date(dateString).toLocaleString();
	}
</script>

<div class="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-7xl mx-auto">
		<!-- Header Area -->
		<div
			class="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-200 pb-6 mb-8 gap-4"
		>
			<div>
				<h1 class="text-3xl font-extrabold tracking-tight text-slate-900">Admin Control Center</h1>
				<p class="mt-1 text-sm text-slate-500">
					Monitor system integrity, manage administrative roles, and inspect operational metrics.
				</p>
			</div>

			<!-- Sliding Tabs Switcher -->
			<div class="relative bg-slate-200/80 p-1 rounded-xl flex w-72 h-11 self-start md:self-auto">
				<!-- Sliding background indicator -->
				<div
					class="absolute top-1 bottom-1 left-1 rounded-lg bg-white shadow-sm transition-all duration-300 ease-out"
					style="width: calc(50% - 4px); transform: translateX({activeTab === 'users'
						? '0'
						: '100%'})"
				></div>

				<!-- Buttons -->
				<button
					class="relative z-10 flex-1 text-center text-sm font-semibold transition-colors duration-200 {activeTab ===
					'users'
						? 'text-slate-900'
						: 'text-slate-500 hover:text-slate-900'}"
					on:click={() => switchTab('users')}
				>
					Users
				</button>
				<button
					class="relative z-10 flex-1 text-center text-sm font-semibold transition-colors duration-200 {activeTab ===
					'health'
						? 'text-slate-900'
						: 'text-slate-500 hover:text-slate-900'}"
					on:click={() => switchTab('health')}
				>
					System Health
				</button>
			</div>
		</div>

		{#if error}
			<div class="bg-rose-50 border-l-4 border-rose-500 p-4 mb-8 rounded-r-xl shadow-sm">
				<div class="flex">
					<div class="flex-shrink-0">
						<svg
							class="h-5 w-5 text-rose-500"
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
					<div class="ml-3">
						<p class="text-sm font-medium text-rose-700">{error}</p>
					</div>
				</div>
			</div>
		{/if}

		<!-- ================= USERS TAB ================= -->
		{#if activeTab === 'users'}
			<div class="space-y-6">
				<!-- Action bar -->
				<div
					class="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-100 shadow-sm"
				>
					<div>
						<h2 class="text-lg font-bold text-slate-900">User Directory</h2>
						<p class="text-xs text-slate-500">Currently active accounts: {users.length}</p>
					</div>
					<button
						on:click={() => (isNewUserModalOpen = true)}
						class="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
					>
						<svg
							class="w-4 h-4 mr-2"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2.5"
								d="M12 4v16m8-8H4"
							/>
						</svg>
						New User
					</button>
				</div>

				{#if isLoading}
					<div
						class="flex flex-col items-center justify-center py-24 bg-white rounded-2xl border border-slate-100 shadow-sm space-y-4"
					>
						<div
							class="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"
						></div>
						<p class="text-slate-400 text-sm">Loading users from backend...</p>
					</div>
				{:else}
					<div class="bg-white border border-slate-100 rounded-2xl shadow-sm overflow-hidden">
						<div class="overflow-x-auto">
							<table class="min-w-full divide-y divide-slate-100">
								<thead class="bg-slate-50/70">
									<tr>
										<th
											scope="col"
											class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider"
											>ID</th
										>
										<th
											scope="col"
											class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider"
											>Name</th
										>
										<th
											scope="col"
											class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider"
											>Email</th
										>
										<th
											scope="col"
											class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider"
											>Username</th
										>
										<th
											scope="col"
											class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider"
											>Last Login</th
										>
										<th
											scope="col"
											class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider"
											>Role</th
										>
									</tr>
								</thead>
								<tbody class="bg-white divide-y divide-slate-100">
									{#each users as user}
										<tr class="hover:bg-slate-50/50 transition-colors">
											<td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-slate-400">
												{user.id}
											</td>
											<td class="px-6 py-4 whitespace-nowrap">
												<div class="flex items-center">
													{#if user.profile_picture_url}
														<img
															class="h-8 w-8 rounded-full mr-3 object-cover border border-slate-200"
															src={user.profile_picture_url}
															alt="Profile"
														/>
													{:else}
														<div
															class="h-8 w-8 rounded-full mr-3 bg-indigo-50 flex items-center justify-center border border-indigo-100 text-xs font-bold text-indigo-700"
														>
															{(user.first_name?.[0] || '') + (user.surname?.[0] || '')}
														</div>
													{/if}
													<div class="text-sm font-bold text-slate-900">
														{user.first_name}
														{user.surname}
													</div>
												</div>
											</td>
											<td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
												{user.email}
											</td>
											<td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
												@{user.username || 'n/a'}
											</td>
											<td class="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
												{formatDate(user.last_login)}
											</td>
											<td class="px-6 py-4 whitespace-nowrap text-sm">
												{#if user.is_superuser}
													<span
														class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-100"
													>
														Admin
													</span>
												{:else}
													<span
														class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100"
													>
														User
													</span>
												{/if}
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{/if}
			</div>
		{/if}

		<!-- ================= SYSTEM HEALTH TAB ================= -->
		{#if activeTab === 'health'}
			<div class="space-y-6">
				<!-- Action bar -->
				<div
					class="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-100 shadow-sm"
				>
					<div>
						<h2 class="text-lg font-bold text-slate-900">Infrastructure Health</h2>
						<p class="text-xs text-slate-500">
							{#if healthData}
								Diagnostics compiled in {healthLatencyMs}ms (API connection active)
							{:else}
								Run diagnostic connectivity suite
							{/if}
						</p>
					</div>
					<button
						on:click={loadHealth}
						disabled={isHealthLoading}
						class="inline-flex items-center px-4 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold rounded-lg shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
					>
						{#if isHealthLoading}
							<div
								class="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin mr-2"
							></div>
							Refreshing...
						{:else}
							<svg
								class="w-4 h-4 mr-2"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
								xmlns="http://www.w3.org/2000/svg"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.2"
								/>
							</svg>
							Refresh Diagnostics
						{/if}
					</button>
				</div>

				{#if healthError}
					<div
						class="bg-rose-50 border-l-4 border-rose-500 p-4 rounded-r-xl shadow-sm text-sm text-rose-700"
					>
						{healthError}
					</div>
				{/if}

				{#if isHealthLoading && !healthData}
					<div
						class="flex flex-col items-center justify-center py-24 bg-white rounded-2xl border border-slate-100 shadow-sm space-y-4"
					>
						<div
							class="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"
						></div>
						<p class="text-slate-400 text-sm">Quering internal and external APIs...</p>
					</div>
				{:else if healthData}
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
						<!-- Core Backend Server Card -->
						<div
							class="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm flex flex-col justify-between"
						>
							<div>
								<div class="flex justify-between items-start mb-4">
									<h3 class="font-bold text-slate-800 text-lg">Backend API</h3>
									<span
										class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-100"
									>
										Healthy
									</span>
								</div>
								<p class="text-xs text-slate-500 mb-4">
									The core FastAPI application handling database and client workflows.
								</p>
								<div
									class="space-y-1.5 font-mono text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100"
								>
									<div class="flex justify-between">
										<span class="text-slate-400">Response Latency:</span>
										<span class="font-semibold text-slate-800">{healthLatencyMs} ms</span>
									</div>
									<div class="flex justify-between">
										<span class="text-slate-400">Environment:</span>
										<span class="font-semibold text-slate-800">Production</span>
									</div>
								</div>
							</div>
						</div>

						<!-- PostgreSQL Database Card -->
						<div
							class="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm flex flex-col justify-between"
						>
							<div>
								<div class="flex justify-between items-start mb-4">
									<h3 class="font-bold text-slate-800 text-lg">PostgreSQL Database</h3>
									{#if healthData.database?.status === 'ok'}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-100"
										>
											Healthy
										</span>
									{:else}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-100"
										>
											Offline
										</span>
									{/if}
								</div>
								<p class="text-xs text-slate-500 mb-4">
									Relational storage module holding user metadata, jobs, and CV data.
								</p>
								<div
									class="space-y-1.5 font-mono text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100"
								>
									{#if healthData.database?.status === 'ok'}
										<div class="flex justify-between">
											<span class="text-slate-400">SQL Latency:</span>
											<span class="font-semibold text-slate-800"
												>{healthData.database.latency_ms} ms</span
											>
										</div>
										<div class="flex justify-between">
											<span class="text-slate-400">PubSub Broker:</span>
											<span class="font-semibold text-slate-800">{healthData.database.pubsub}</span>
										</div>
									{:else}
										<div class="text-rose-600 text-xs font-semibold">
											{healthData.database?.message || 'Connection failed'}
										</div>
									{/if}
								</div>
							</div>
						</div>

						<!-- Temporal Orchestrator Card -->
						<div
							class="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm flex flex-col justify-between"
						>
							<div>
								<div class="flex justify-between items-start mb-4">
									<h3 class="font-bold text-slate-800 text-lg">Temporal.io</h3>
									{#if healthData.temporal?.status === 'ok'}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-100"
										>
											Healthy
										</span>
									{:else}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-100"
										>
											Offline
										</span>
									{/if}
								</div>
								<p class="text-xs text-slate-500 mb-4">
									Workflow management and background job execution orchestrator.
								</p>
								<div
									class="space-y-1.5 font-mono text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100 font-mono"
								>
									{#if healthData.temporal?.status === 'ok'}
										<div class="flex justify-between">
											<span class="text-slate-400">Host:</span>
											<span class="font-semibold text-slate-800 truncate max-w-[120px]"
												>{healthData.temporal.host}</span
											>
										</div>
										<div class="flex justify-between">
											<span class="text-slate-400">Namespace:</span>
											<span class="font-semibold text-slate-800"
												>{healthData.temporal.namespace}</span
											>
										</div>
									{:else}
										<div class="text-rose-600 text-xs font-semibold truncate">
											{healthData.temporal?.message || 'Connection failed'}
										</div>
									{/if}
								</div>
							</div>
						</div>

						<!-- Ollama Local LLM Card -->
						<div
							class="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm flex flex-col justify-between"
						>
							<div>
								<div class="flex justify-between items-start mb-4">
									<h3 class="font-bold text-slate-800 text-lg">Ollama (LLM)</h3>
									{#if healthData.ollama?.status === 'ok'}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-100"
										>
											Connected
										</span>
									{:else}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-100"
										>
											Offline
										</span>
									{/if}
								</div>
								<p class="text-xs text-slate-500 mb-4">
									Local LLM generation services for automated CV tuning.
								</p>
								<div
									class="space-y-1.5 font-mono text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100 font-mono"
								>
									{#if healthData.ollama?.status === 'ok'}
										<div class="flex justify-between">
											<span class="text-slate-400">Model Name:</span>
											<span class="font-semibold text-slate-800"
												>{healthData.ollama.configured_model}</span
											>
										</div>
										<div class="flex justify-between">
											<span class="text-slate-400">Model Pulled:</span>
											<span
												class="font-semibold {healthData.ollama.model_ready
													? 'text-emerald-600 font-bold'
													: 'text-amber-600 font-bold'}"
											>
												{healthData.ollama.model_ready ? 'Ready' : 'Not Loaded'}
											</span>
										</div>
										<div class="flex justify-between border-t border-slate-200/50 pt-1.5 mt-1.5">
											<span class="text-slate-400">Inference Test:</span>
											{#if healthData.ollama.inference_status === 'ok'}
												<span class="text-emerald-600 font-bold">Passed</span>
											{:else}
												<span class="text-rose-600 font-bold">Failed</span>
											{/if}
										</div>
										{#if healthData.ollama.inference_status !== 'ok'}
											<div class="text-rose-600 text-[10px] leading-relaxed mt-1 break-words">
												Error: {healthData.ollama.inference_error}
											</div>
										{/if}
									{:else}
										<div class="text-rose-600 text-xs font-semibold truncate">
											{healthData.ollama?.message || 'Connection failed'}
										</div>
									{/if}
								</div>
							</div>
						</div>

						<!-- Cloud Provider Health Card -->
						<div
							class="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm flex flex-col justify-between"
						>
							<div>
								<h3 class="font-bold text-slate-800 text-lg mb-4">Cloud Providers</h3>
								<p class="text-xs text-slate-500 mb-4">
									Status of external cloud inference and image processing vendors.
								</p>
								<div class="space-y-3 text-xs bg-slate-50 p-3 rounded-lg border border-slate-100">
									<!-- Groq -->
									<div class="flex flex-col space-y-1 pb-2 border-b border-slate-200/50">
										<div class="flex items-center justify-between">
											<span class="font-semibold text-slate-700">Groq:</span>
											{#if healthData.providers?.groq?.status === 'ok'}
												<span
													class="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 font-mono"
													>{healthData.providers.groq.latency_ms} ms</span
												>
											{:else if healthData.providers?.groq?.status === 'skipped'}
												<span
													class="text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200"
													>Skipped</span
												>
											{:else}
												<span
													class="text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-100"
													>Error</span
												>
											{/if}
										</div>
										{#if healthData.providers?.groq?.status === 'ok'}
											<div class="flex items-center justify-between text-[11px]">
												<span class="text-slate-400">Inference Check:</span>
												{#if healthData.providers.groq.inference_status === 'ok'}
													<span class="text-emerald-600 font-semibold">Passed</span>
												{:else}
													<span class="text-rose-600 font-semibold">Failed</span>
												{/if}
											</div>
											{#if healthData.providers.groq.inference_status !== 'ok'}
												<div
													class="text-rose-600 text-[10px] leading-relaxed break-words font-mono mt-0.5"
												>
													Error: {healthData.providers.groq.inference_error}
												</div>
											{/if}
										{/if}
									</div>

									<!-- OpenRouter -->
									<div class="flex flex-col space-y-1 pb-2 border-b border-slate-200/50">
										<div class="flex items-center justify-between">
											<span class="font-semibold text-slate-700">OpenRouter:</span>
											{#if healthData.providers?.openrouter?.status === 'ok'}
												<span
													class="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 font-mono"
													>{healthData.providers.openrouter.latency_ms} ms</span
												>
											{:else if healthData.providers?.openrouter?.status === 'skipped'}
												<span
													class="text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200"
													>Skipped</span
												>
											{:else}
												<span
													class="text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-100"
													>Error</span
												>
											{/if}
										</div>
										{#if healthData.providers?.openrouter?.status === 'ok'}
											<div class="flex items-center justify-between text-[11px]">
												<span class="text-slate-400">Inference Check:</span>
												{#if healthData.providers.openrouter.inference_status === 'ok'}
													<span class="text-emerald-600 font-semibold">Passed</span>
												{:else}
													<span class="text-rose-600 font-semibold">Failed</span>
												{/if}
											</div>
											{#if healthData.providers.openrouter.inference_status !== 'ok'}
												<div
													class="text-rose-600 text-[10px] leading-relaxed break-words font-mono mt-0.5"
												>
													Error: {healthData.providers.openrouter.inference_error}
												</div>
											{/if}
										{/if}
									</div>

									<!-- Cloudinary -->
									<div class="flex items-center justify-between">
										<span class="font-semibold text-slate-700">Cloudinary:</span>
										{#if healthData.cloudinary?.status === 'ok'}
											<span
												class="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 font-mono"
												>{healthData.cloudinary.latency_ms} ms</span
											>
										{:else if healthData.cloudinary?.status === 'skipped'}
											<span
												class="text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200"
												>Skipped</span
											>
										{:else}
											<span
												class="text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-100 font-mono"
												>Offline</span
											>
										{/if}
									</div>
								</div>
							</div>
						</div>

						<!-- CV Parsing API Card -->
						<div
							class="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm flex flex-col justify-between"
						>
							<div>
								<div class="flex justify-between items-start mb-4">
									<h3 class="font-bold text-slate-800 text-lg">LlamaCloud (CV Parsing)</h3>
									{#if healthData.llamacloud?.status === 'ok'}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-100"
										>
											Online
										</span>
									{:else if healthData.llamacloud?.status === 'skipped'}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200"
										>
											Skipped
										</span>
									{:else}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-100"
										>
											Offline
										</span>
									{/if}
								</div>
								<p class="text-xs text-slate-500 mb-4">
									External document indexing API utilized for structuring CV layouts.
								</p>
								<div
									class="space-y-1.5 font-mono text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100"
								>
									{#if healthData.llamacloud?.status === 'ok'}
										<div class="flex justify-between">
											<span class="text-slate-400">API Status Code:</span>
											<span class="font-semibold text-slate-800"
												>{healthData.llamacloud.status_code}</span
											>
										</div>
										<div class="flex justify-between">
											<span class="text-slate-400">Response time:</span>
											<span class="font-semibold text-slate-800"
												>{healthData.llamacloud.latency_ms} ms</span
											>
										</div>
									{:else}
										<div class="text-slate-500 text-xs truncate">
											{healthData.llamacloud?.message || 'No API key provided'}
										</div>
									{/if}
								</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<!-- ================= NEW USER MODAL ================= -->
{#if isNewUserModalOpen}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm"
		on:click|self={() => (isNewUserModalOpen = false)}
	>
		<div
			class="bg-white rounded-2xl shadow-xl border border-slate-100 max-w-md w-full mx-4 overflow-hidden transform transition-all"
		>
			<!-- Header -->
			<div
				class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50"
			>
				<div>
					<h3 class="text-lg font-bold text-slate-950">Add Account</h3>
					<p class="text-xs text-slate-500">
						Provide user credentials to create a new system profile.
					</p>
				</div>
				<button
					on:click={() => (isNewUserModalOpen = false)}
					class="text-slate-400 hover:text-slate-600 transition-colors p-1.5 rounded-lg hover:bg-slate-100"
				>
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
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<!-- Body -->
			<form on:submit|preventDefault={handleCreateUser} class="p-6 space-y-4">
				{#if userFormError}
					<div
						class="bg-rose-50 border border-rose-100 p-3 rounded-lg text-xs text-rose-700 font-medium"
					>
						{userFormError}
					</div>
				{/if}
				{#if userFormSuccess}
					<div
						class="bg-emerald-50 border border-emerald-100 p-3 rounded-lg text-xs text-emerald-700 font-medium"
					>
						{userFormSuccess}
					</div>
				{/if}

				<div class="grid grid-cols-2 gap-4">
					<div>
						<label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1"
							>First Name</label
						>
						<input
							type="text"
							bind:value={firstName}
							required
							class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm bg-slate-50/50"
						/>
					</div>
					<div>
						<label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1"
							>Surname</label
						>
						<input
							type="text"
							bind:value={surname}
							required
							class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm bg-slate-50/50"
						/>
					</div>
				</div>

				<div>
					<label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1"
						>Email Address</label
					>
					<input
						type="email"
						bind:value={email}
						required
						class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm bg-slate-50/50"
					/>
				</div>

				<div>
					<label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1"
						>Username</label
					>
					<input
						type="text"
						bind:value={username}
						required
						class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm bg-slate-50/50"
					/>
				</div>

				<div>
					<label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1"
						>Password</label
					>
					<input
						type="password"
						bind:value={password}
						required
						minlength="6"
						class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm bg-slate-50/50"
					/>
				</div>

				<div class="flex items-center pt-2">
					<input
						id="superuser-checkbox"
						type="checkbox"
						bind:checked={isSuperuser}
						class="h-4 w-4 text-indigo-600 focus:ring-indigo-500/20 border-slate-300 rounded"
					/>
					<label for="superuser-checkbox" class="ml-2 block text-xs font-semibold text-slate-700">
						Assign Administrator role (`is_superuser`)
					</label>
				</div>

				<!-- Footer -->
				<div class="pt-4 border-t border-slate-100 flex justify-end space-x-3 mt-6">
					<button
						type="button"
						on:click={() => (isNewUserModalOpen = false)}
						class="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 text-sm font-semibold transition-colors"
					>
						Cancel
					</button>
					<button
						type="submit"
						disabled={isSubmittingUser}
						class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
					>
						{#if isSubmittingUser}Creating...{:else}Create User{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
