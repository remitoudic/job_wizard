<script lang="ts">
    import { registerUser } from "$lib/api";
    import { goto } from "$app/navigation";

    let email = "";
    let username = "";
    let password = "";
    let error = "";
    let isLoading = false;

    async function handleSubmit() {
        isLoading = true;
        error = "";

        try {
            await registerUser({ email, username, password });
            goto("/login");
        } catch (e: any) {
            error = e.message || "Registration failed";
        } finally {
            isLoading = false;
        }
    }
</script>

<div
    class="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md border border-gray-100"
>
    <h1 class="text-2xl font-bold mb-6 text-gray-800 text-center">Register</h1>

    {#if error}
        <div class="mb-4 p-3 bg-red-50 text-red-600 rounded text-sm">
            {error}
        </div>
    {/if}

    <form on:submit|preventDefault={handleSubmit} class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1"
                >Email</label
            >
            <input
                type="email"
                bind:value={email}
                required
                class="w-full px-3 py-2 border rounded-md focus:ring-primary-500 focus:border-primary-500"
            />
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1"
                >Username</label
            >
            <input
                type="text"
                bind:value={username}
                required
                class="w-full px-3 py-2 border rounded-md focus:ring-primary-500 focus:border-primary-500"
            />
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1"
                >Password</label
            >
            <input
                type="password"
                bind:value={password}
                required
                class="w-full px-3 py-2 border rounded-md focus:ring-primary-500 focus:border-primary-500"
            />
        </div>

        <button
            type="submit"
            disabled={isLoading}
            class="w-full py-2 px-4 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
            {isLoading ? "Creating account..." : "Register"}
        </button>
    </form>

    <div class="mt-4 text-center text-sm text-gray-600">
        Already have an account? <a
            href="/login"
            class="text-primary-600 hover:underline">Login</a
        >
    </div>
</div>
