<script lang="ts">
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { auth } from "../../stores/auth";

    function handleLogout() {
        auth.logout();
        goto("/login");
    }

    // Check if a path is active
    function isActive(path: string): boolean {
        return $page.url.pathname === path;
    }
</script>

<!-- Desktop Sidebar -->
<aside
    class="hidden md:flex fixed left-0 top-0 h-screen w-16 bg-[#0F172A] flex-col items-center py-6 gap-8 z-40"
>
    <!-- Logo/Home Icon -->
    <a
        href="/"
        class="p-2 text-[#64748B] hover:text-[#0369A1] transition-all duration-200 hover:scale-110 group relative"
        title="Home"
    >
        <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
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
        <!-- Tooltip -->
        <span
            class="absolute left-full ml-4 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none"
        >
            Home
        </span>
    </a>

    <!-- Divider -->
    <div class="w-8 h-[1px] bg-[#334155]"></div>

    <!-- Navigation Items -->
    <nav class="flex flex-col gap-4 flex-1">
        <!-- Applications -->
        <a
            href="/applications"
            class="relative p-2 text-[#64748B] hover:text-[#0369A1] transition-all duration-200 hover:scale-110 group {isActive(
                '/applications',
            )
                ? 'text-[#0369A1]'
                : ''}"
            title="Applications"
        >
            {#if isActive("/applications")}
                <div
                    class="absolute left-0 top-0 bottom-0 w-1 bg-[#0369A1] rounded-r"
                ></div>
            {/if}
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
            </svg>
            <!-- Tooltip -->
            <span
                class="absolute left-full ml-4 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none"
            >
                Applications
            </span>
        </a>

        <!-- Profile -->
        <a
            href="/profile"
            class="relative p-2 text-[#64748B] hover:text-[#0369A1] transition-all duration-200 hover:scale-110 group {isActive(
                '/profile',
            )
                ? 'text-[#0369A1]'
                : ''}"
            title="Profile"
        >
            {#if isActive("/profile")}
                <div
                    class="absolute left-0 top-0 bottom-0 w-1 bg-[#0369A1] rounded-r"
                ></div>
            {/if}
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
            </svg>
            <!-- Tooltip -->
            <span
                class="absolute left-full ml-4 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none"
            >
                Profile
            </span>
        </a>
        <!-- Why use this? -->
        <a
            href="/why"
            class="relative p-2 text-[#64748B] hover:text-[#0369A1] transition-all duration-200 hover:scale-110 group {isActive(
                '/why',
            )
                ? 'text-[#0369A1]'
                : ''}"
            title="Why use this?"
        >
            {#if isActive("/why")}
                <div
                    class="absolute left-0 top-0 bottom-0 w-1 bg-[#0369A1] rounded-r"
                ></div>
            {/if}
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
            </svg>
            <!-- Tooltip -->
            <span
                class="absolute left-full ml-4 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none"
            >
                Why use this?
            </span>
        </a>

        <!-- Admin (Superuser only) -->
        {#if $auth.user?.is_superuser}
            <a
                href="/admin"
                class="relative p-2 text-[#64748B] hover:text-[#0369A1] transition-all duration-200 hover:scale-110 group {isActive(
                    '/admin',
                )
                    ? 'text-[#0369A1]'
                    : ''}"
                title="Admin"
            >
                {#if isActive("/admin")}
                    <div
                        class="absolute left-0 top-0 bottom-0 w-1 bg-[#0369A1] rounded-r"
                    ></div>
                {/if}
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                </svg>
                <!-- Tooltip -->
                <span
                    class="absolute left-full ml-4 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none"
                >
                    Admin
                </span>
            </a>
        {/if}
    </nav>

    <!-- Logout (at bottom) -->
    <button
        on:click={handleLogout}
        class="p-2 text-[#64748B] hover:text-[#EF4444] transition-all duration-200 hover:scale-110 group relative"
        title="Logout"
    >
        <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
        >
            <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
        </svg>
        <!-- Tooltip -->
        <span
            class="absolute left-full ml-4 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none"
        >
            Logout
        </span>
    </button>
</aside>

<!-- Mobile Bottom Navigation -->
<nav
    class="md:hidden fixed bottom-0 left-0 right-0 bg-[#0F172A] border-t border-[#334155] z-40 safe-area-inset-bottom"
>
    <div class="flex justify-around items-center h-16 px-4">
        <!-- Applications -->
        <a
            href="/applications"
            class="flex flex-col items-center gap-1 p-2 text-[#64748B] hover:text-[#0369A1] transition-colors {isActive(
                '/applications',
            )
                ? 'text-[#0369A1]'
                : ''}"
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
            </svg>
            <span class="text-[10px] font-medium">Applications</span>
        </a>

        <!-- Profile -->
        <a
            href="/profile"
            class="flex flex-col items-center gap-1 p-2 text-[#64748B] hover:text-[#0369A1] transition-colors {isActive(
                '/profile',
            )
                ? 'text-[#0369A1]'
                : ''}"
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
            </svg>
            <span class="text-[10px] font-medium">Profile</span>
        </a>

        <!-- Why -->
        <a
            href="/why"
            class="flex flex-col items-center gap-1 p-2 text-[#64748B] hover:text-[#0369A1] transition-colors {isActive(
                '/why',
            )
                ? 'text-[#0369A1]'
                : ''}"
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
            </svg>
            <span class="text-[10px] font-medium">Why</span>
        </a>

        <!-- Admin (Superuser only) -->
        {#if $auth.user?.is_superuser}
            <a
                href="/admin"
                class="flex flex-col items-center gap-1 p-2 text-[#64748B] hover:text-[#0369A1] transition-colors {isActive(
                    '/admin',
                )
                    ? 'text-[#0369A1]'
                    : ''}"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                </svg>
                <span class="text-[10px] font-medium">Admin</span>
            </a>
        {/if}

        <!-- Logout -->
        <button
            on:click={handleLogout}
            class="flex flex-col items-center gap-1 p-2 text-[#64748B] hover:text-[#EF4444] transition-colors"
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
            </svg>
            <span class="text-[10px] font-medium">Logout</span>
        </button>
    </div>
</nav>
