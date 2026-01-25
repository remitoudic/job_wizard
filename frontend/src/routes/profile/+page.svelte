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
    let isAddressOpen = false;
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

    <div
        class="mb-6 p-4 bg-blue-50 text-blue-800 rounded-lg text-sm border border-blue-100 flex items-start gap-3"
    >
        <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 text-blue-500 mt-0.5 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
        >
            <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
        </svg>
        <p>
            The contact information will be used for the header of covering
            letter, and will be used only for this purpose.
        </p>
    </div>

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
                        >First Name</label
                    >
                    <input
                        type="text"
                        bind:value={user.first_name}
                        class="input w-full"
                        placeholder="John"
                    />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1"
                        >Surname</label
                    >
                    <input
                        type="text"
                        bind:value={user.surname}
                        class="input w-full"
                        placeholder="Doe"
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

                <div class="md:col-span-2 pt-4">
                    <button
                        type="button"
                        on:click={() => (isAddressOpen = !isAddressOpen)}
                        class="flex items-center justify-between w-full text-left text-lg font-medium text-gray-900 border-b border-gray-100 pb-2 mb-4 hover:bg-gray-50 transition-colors"
                    >
                        <span>Address</span>
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            class="h-5 w-5 transform transition-transform {isAddressOpen
                                ? 'rotate-180'
                                : ''}"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M19 9l-7 7-7-7"
                            />
                        </svg>
                    </button>
                </div>

                {#if isAddressOpen}
                    <div class="md:col-span-2 contents">
                        <div class="md:col-span-2">
                            <label
                                class="block text-sm font-medium text-gray-700 mb-1"
                                >Street</label
                            >
                            <input
                                type="text"
                                bind:value={user.street}
                                class="input w-full"
                                placeholder="123 Main St"
                            />
                        </div>
                        <div>
                            <label
                                class="block text-sm font-medium text-gray-700 mb-1"
                                >City</label
                            >
                            <input
                                type="text"
                                bind:value={user.city}
                                class="input w-full"
                                placeholder="New York"
                            />
                        </div>
                        <div>
                            <label
                                class="block text-sm font-medium text-gray-700 mb-1"
                                >Postcode</label
                            >
                            <input
                                type="text"
                                bind:value={user.postcode}
                                class="input w-full"
                                placeholder="10001"
                            />
                        </div>
                        <div class="md:col-span-2">
                            <label
                                class="block text-sm font-medium text-gray-700 mb-1"
                                >Country</label
                            >
                            <input
                                type="text"
                                bind:value={user.country}
                                class="input w-full"
                                placeholder="USA"
                            />
                        </div>
                    </div>
                {/if}
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
