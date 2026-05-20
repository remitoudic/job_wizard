<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '../../stores/auth';
	import { getUsers, type User } from '$lib/api';

	export let data: any = {};
	export let params: Record<string, string> = {};

	let users: User[] = [];
	let error = '';
	let isLoading = true;

	onMount(async () => {
		// Wait a bit for auth.initialize() to complete
		await new Promise((resolve) => setTimeout(resolve, 500));

		if (!$auth.isAuthenticated || !$auth.user?.is_superuser) {
			console.log('Auth check failed:', {
				isAuthenticated: $auth.isAuthenticated,
				user: $auth.user,
				is_superuser: $auth.user?.is_superuser
			});
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

	function formatDate(dateString?: string) {
		if (!dateString) return 'Never';
		return new Date(dateString).toLocaleString();
	}
</script>

<div class="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-7xl mx-auto">
		<h1 class="text-3xl font-bold text-gray-900 mb-8">Admin Dashboard</h1>

		{#if error}
			<div class="bg-red-50 border-l-4 border-red-400 p-4 mb-8">
				<div class="flex">
					<div class="ml-3">
						<p class="text-sm text-red-700">{error}</p>
					</div>
				</div>
			</div>
		{/if}

		{#if isLoading}
			<div class="text-center py-12">
				<p class="text-gray-500">Loading users...</p>
			</div>
		{:else}
			<div class="bg-white shadow overflow-hidden sm:rounded-lg">
				<div class="overflow-x-auto">
					<table class="min-w-full divide-y divide-gray-200">
						<thead class="bg-gray-50">
							<tr>
								<th
									scope="col"
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
								>
									ID
								</th>
								<th
									scope="col"
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
								>
									Name
								</th>
								<th
									scope="col"
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
								>
									Email
								</th>
								<th
									scope="col"
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
								>
									Username
								</th>
								<th
									scope="col"
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
								>
									Last Login
								</th>
								<th
									scope="col"
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
								>
									Role
								</th>
							</tr>
						</thead>
						<tbody class="bg-white divide-y divide-gray-200">
							{#each users as user}
								<tr>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
										{user.id}
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<div class="text-sm font-medium text-gray-900">
											{user.first_name}
											{user.surname}
										</div>
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<div class="text-sm text-gray-900">
											{user.email}
										</div>
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
										{user.username}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
										{formatDate(user.last_login)}
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										{#if user.is_superuser}
											<span
												class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-purple-100 text-purple-800"
											>
												Admin
											</span>
										{:else}
											<span
												class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800"
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
</div>
