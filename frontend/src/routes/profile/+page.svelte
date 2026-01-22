<script lang="ts">
    import { onMount } from "svelte";
    import { getProfile, updateProfile } from "$lib/api";
    import { auth } from "../../stores/auth";
    import type { User } from "../../stores/auth";

    // SvelteKit may pass `data` and `params` to pages — declare to prevent runtime warnings
    export let data: any = {};
    export let params: Record<string, string> = {};

    let user: User | null = null;
    let isLoading = true;
    let isSaving = false;
    let message = "";
    let error = "";

    onMount(async () => {
        try {
            user = await getProfile();
            auth.updateUser(user!);
        } catch (e) {
            error = "Failed to load profile";
        } finally {
            isLoading = false;
        }
    });

    async function handleSave() {
        if (!user) return;
        isSaving = true;
        message = "";
        error = "";

        try {
            const updatedUser = await updateProfile(user);
            user = updatedUser;
            auth.updateUser(user!);
            message = "Profile updated successfully!";
        } catch (e: any) {
            error = e.message || "Failed to update profile";
        } finally {
            isSaving = false;
        }
    }
</script>

<div
    class="max-w-2xl mx-auto mt-8 p-6 bg-white rounded-lg shadow-md border border-gray-100"
>
    <h1 class="text-2xl font-bold mb-6 text-gray-800">My Profile</h1>

    {#if isLoading}
        <div class="text-center py-10 text-gray-500">Loading profile...</div>
    {:else if user}
        {#if message}
            <div
                class="mb-4 p-3 bg-green-50 text-green-700 rounded text-sm border border-green-200"
            >
                {message}
            </div>
        {/if}
        {#if error}
            <div
                class="mb-4 p-3 bg-red-50 text-red-600 rounded text-sm border border-red-200"
            >
                {error}
            </div>
        {/if}

        <form on:submit|preventDefault={handleSave} class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1"
                        >Full Name</label
                    >
                    <input
                        type="text"
                        bind:value={user.full_name}
                        class="input w-full"
                        placeholder="John Doe"
                    />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1"
                        >Job Title</label
                    >
                    <input
                        type="text"
                        bind:value={user.job_title}
                        class="input w-full"
                        placeholder="Software Engineer"
                    />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1"
                        >Email</label
                    >
                    <input
                        type="email"
                        value={user.email}
                        disabled
                        class="input w-full bg-gray-50 text-gray-500 cursor-not-allowed"
                    />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1"
                        >Phone</label
                    >
                    <input
                        type="text"
                        bind:value={user.phone}
                        class="input w-full"
                        placeholder="+1 234 567 8900"
                    />
                </div>
                <div class="md:col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1"
                        >LinkedIn URL</label
                    >
                    <input
                        type="url"
                        bind:value={user.linkedin_url}
                        class="input w-full"
                        placeholder="https://linkedin.com/in/..."
                    />
                </div>
                <div class="md:col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1"
                        >Portfolio URL</label
                    >
                    <input
                        type="url"
                        bind:value={user.portfolio_url}
                        class="input w-full"
                        placeholder="https://myportfolio.com"
                    />
                </div>
            </div>

            <div class="pt-4 border-t border-gray-100 flex justify-end">
                <button
                    type="submit"
                    disabled={isSaving}
                    class="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                    {isSaving ? "Saving..." : "Save Changes"}
                </button>
            </div>
        </form>
    {:else}
        <div class="text-center py-10">
            <p class="text-gray-500 mb-4">
                You need to be logged in to view this page.
            </p>
            <a href="/login" class="text-primary-600 hover:underline"
                >Go to Login</a
            >
        </div>
    {/if}
</div>

<style>
    .input {
        @apply px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 transition-colors;
    }
</style>
