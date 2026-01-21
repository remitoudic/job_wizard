<script lang="ts">
    import { registerUser } from "$lib/api";
    import { goto } from "$app/navigation";

    let email = "";
    let username = "";
    let password = "";
    let confirmPassword = "";
    let error = "";
    let isLoading = false;
    let showPassword = false;
    let showConfirmPassword = false;

    async function handleSubmit() {
        isLoading = true;
        error = "";

        // Validate passwords match
        if (password !== confirmPassword) {
            error = "Passwords do not match";
            isLoading = false;
            return;
        }

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

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
                Confirm Password
            </label>
            <div class="relative">
                <input
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    on:input={(e) => (confirmPassword = e.currentTarget.value)}
                    required
                    class="w-full px-3 py-2 border rounded-md focus:ring-primary-500 focus:border-primary-500"
                />
                <button
                    type="button"
                    on:click={() =>
                        (showConfirmPassword = !showConfirmPassword)}
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-600 hover:text-gray-800"
                    title={showConfirmPassword
                        ? "Hide password"
                        : "Show password"}
                >
                    {showConfirmPassword ? "🙈" : "👁️"}
                </button>
            </div>
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
