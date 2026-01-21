<script lang="ts">
    import { loginUser } from "$lib/api";
    import { auth } from "../../stores/auth";
    import { goto } from "$app/navigation";

    let email = "";
    let password = "";
    let error = "";
    let isLoading = false;
    let showPassword = false;

    async function handleSubmit() {
        isLoading = true;
        error = "";

        try {
            const formData = new FormData();
            formData.append("username", email); // OAuth2 expects 'username' field
            formData.append("password", password);

            const data = await loginUser(formData);

            // Fetch complete user profile to get is_superuser and other fields
            const apiUrl = `${window.location.protocol}//${window.location.hostname}:8000`;
            const profileResponse = await fetch(`${apiUrl}/api/users/me`, {
                headers: {
                    Authorization: `Bearer ${data.access_token}`,
                },
            });

            if (!profileResponse.ok) {
                throw new Error("Failed to fetch user profile");
            }

            const user = await profileResponse.json();
            auth.login(data.access_token, user);

            // Redirect to home
            goto("/");
        } catch (e: any) {
            error = e.message || "Login failed";
        } finally {
            isLoading = false;
        }
    }
</script>

<div
    class="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md border border-gray-100"
>
    <h1 class="text-2xl font-bold mb-6 text-gray-800 text-center">Login</h1>

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
                placeholder="you@example.com"
            />
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
                Password
            </label>
            <div class="relative">
                <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    on:input={(e) => (password = e.currentTarget.value)}
                    required
                    class="w-full px-3 py-2 border rounded-md focus:ring-primary-500 focus:border-primary-500"
                    placeholder="••••••••"
                />
                <button
                    type="button"
                    on:click={() => (showPassword = !showPassword)}
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-600 hover:text-gray-800"
                    title={showPassword ? "Hide password" : "Show password"}
                >
                    {showPassword ? "🙈" : "👁️"}
                </button>
            </div>
        </div>

        <button
            type="submit"
            disabled={isLoading}
            class="w-full py-2 px-4 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
            {isLoading ? "Logging in..." : "Login"}
        </button>
    </form>

    <div class="mt-4 text-center text-sm text-gray-600">
        Don't have an account? <a
            href="/register"
            class="text-primary-600 hover:underline">Register</a
        >
    </div>
</div>
