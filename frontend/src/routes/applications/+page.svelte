<script lang="ts">
    import { onMount } from "svelte";
    import { fetchUserApplications, type ApplicationListItem } from "$lib/api";
    import { auth } from "../../stores/auth";
    import { goto } from "$app/navigation";

    // SvelteKit may pass `data` and `params` to pages — declare to prevent runtime warnings
    export let data: any = {};
    export let params: Record<string, string> = {};

    let applications: ApplicationListItem[] = [];
    let isLoading = true;
    let error = "";
    let expandedId: number | null = null;

    onMount(async () => {
        // Check if user is logged in
        if (!$auth.token) {
            goto("/login");
            return;
        }

        try {
            const response = await fetchUserApplications();
            applications = response.applications;
        } catch (e: any) {
            error = e.message || "Failed to load applications";
        } finally {
            isLoading = false;
        }
    });

    function toggleExpand(id: number) {
        expandedId = expandedId === id ? null : id;
    }

    function formatDate(isoString: string): string {
        const date = new Date(isoString);
        return date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
        });
    }

    function getStatusColor(status: string): string {
        const colors: Record<string, string> = {
            applied: "bg-blue-100 text-blue-800",
            waiting: "bg-yellow-100 text-yellow-800",
            interview: "bg-green-100 text-green-800",
            refused: "bg-red-100 text-red-800",
            accepted: "bg-emerald-100 text-emerald-800",
            finish: "bg-gray-100 text-gray-800",
        };
        return colors[status] || "bg-gray-100 text-gray-800";
    }
</script>

<svelte:head>
    <title>My Applications - Job Wizard</title>
</svelte:head>

<div class="min-h-screen py-16 px-4 bg-gradient-to-b from-white to-slate-50">
    <div class="max-w-4xl mx-auto">
        <!-- Header -->
        <div class="mb-12">
            <a
                href="/"
                class="inline-flex items-center gap-2 text-[#0369A1] hover:text-[#0284C7] transition-colors mb-6"
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
                        d="M10 19l-7-7m0 0l7-7m-7 7h18"
                    />
                </svg>
                <span class="font-semibold">Back to Job Wizard</span>
            </a>
            <h1 class="text-4xl font-extrabold text-[#0F172A] mb-2">
                My Applications
            </h1>
            <p class="text-[#334155]">
                Track your job applications and cover letters
            </p>
        </div>

        <!-- Loading State -->
        {#if isLoading}
            <div class="flex items-center justify-center py-20">
                <svg
                    class="animate-spin h-10 w-10 text-[#0369A1]"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                >
                    <circle
                        class="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        stroke-width="4"
                    ></circle>
                    <path
                        class="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                </svg>
            </div>
        {/if}

        <!-- Error State -->
        {#if error}
            <div
                class="p-6 bg-red-50 border border-red-100 text-red-700 rounded-lg text-center"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-12 w-12 mx-auto mb-3 text-red-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                </svg>
                <p class="font-semibold">{error}</p>
            </div>
        {/if}

        <!-- Empty State -->
        {#if !isLoading && !error && applications.length === 0}
            <div
                class="py-20 text-center bg-white rounded-xl border border-[#E2E8F0] shadow-sm"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-16 w-16 mx-auto mb-4 text-[#94A3B8]"
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
                <h2 class="text-2xl font-bold text-[#0F172A] mb-2">
                    No Applications Yet
                </h2>
                <p class="text-[#64748B] mb-6">
                    Start applying to jobs with Job Wizard to see them here
                </p>
            </div>
        {/if}

        <!-- Applications List -->
        {#if !isLoading && !error && applications.length > 0}
            <div class="space-y-4">
                {#each applications as app (app.id)}
                    <div
                        class="bg-white rounded-lg border border-[#E2E8F0] shadow-sm hover:shadow-md transition-all cursor-pointer overflow-hidden"
                        on:click={() => toggleExpand(app.id)}
                        on:keydown={(e) =>
                            e.key === "Enter" && toggleExpand(app.id)}
                        role="button"
                        tabindex="0"
                    >
                        <!-- Card Header -->
                        <div class="p-6">
                            <div class="flex items-start justify-between">
                                <div class="flex-1">
                                    <h3
                                        class="text-xl font-bold text-[#0F172A] mb-1"
                                    >
                                        {app.job_title}
                                    </h3>
                                    <p class="text-[#64748B] mb-3">
                                        {app.company}
                                    </p>
                                    <div
                                        class="flex items-center gap-3 text-sm"
                                    >
                                        <span class="text-[#64748B]">
                                            {formatDate(app.created_at)}
                                        </span>
                                        <span
                                            class="px-3 py-1 rounded-full text-xs font-semibold uppercase {getStatusColor(
                                                app.status,
                                            )}"
                                        >
                                            {app.status}
                                        </span>
                                    </div>
                                </div>
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    class="h-6 w-6 text-[#64748B] transition-transform {expandedId ===
                                    app.id
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
                            </div>
                        </div>

                        <!-- Expanded Content -->
                        {#if expandedId === app.id}
                            <div
                                class="px-6 pb-6 border-t border-[#E2E8F0] pt-6 space-y-6"
                            >
                                <!-- Cover Letter -->
                                <div>
                                    <h4
                                        class="text-sm font-bold uppercase tracking-wider text-[#64748B] mb-3"
                                    >
                                        Cover Letter
                                    </h4>
                                    <div
                                        class="bg-[#F8FAFC] rounded-lg p-4 border border-[#E2E8F0]"
                                    >
                                        <p
                                            class="text-[#334155] whitespace-pre-wrap leading-relaxed"
                                        >
                                            {app.cover_letter_final.body ||
                                                "No cover letter body available"}
                                        </p>
                                    </div>
                                </div>

                                <!-- Header Information -->
                                {#if app.header && Object.keys(app.header).length > 0}
                                    <div>
                                        <h4
                                            class="text-sm font-bold uppercase tracking-wider text-[#64748B] mb-3"
                                        >
                                            Contact Information
                                        </h4>
                                        <div
                                            class="grid grid-cols-1 md:grid-cols-2 gap-3 bg-[#F8FAFC] rounded-lg p-4 border border-[#E2E8F0]"
                                        >
                                            {#if app.header.name}
                                                <div>
                                                    <span
                                                        class="text-xs font-semibold text-[#64748B]"
                                                        >Name:</span
                                                    >
                                                    <p class="text-[#0F172A]">
                                                        {app.header.name}
                                                    </p>
                                                </div>
                                            {/if}
                                            {#if app.header.email}
                                                <div>
                                                    <span
                                                        class="text-xs font-semibold text-[#64748B]"
                                                        >Email:</span
                                                    >
                                                    <p class="text-[#0F172A]">
                                                        {app.header.email}
                                                    </p>
                                                </div>
                                            {/if}
                                            {#if app.header.phone}
                                                <div>
                                                    <span
                                                        class="text-xs font-semibold text-[#64748B]"
                                                        >Phone:</span
                                                    >
                                                    <p class="text-[#0F172A]">
                                                        {app.header.phone}
                                                    </p>
                                                </div>
                                            {/if}
                                            {#if app.header.address}
                                                <div>
                                                    <span
                                                        class="text-xs font-semibold text-[#64748B]"
                                                        >Address:</span
                                                    >
                                                    <p class="text-[#0F172A]">
                                                        {app.header.address}
                                                    </p>
                                                </div>
                                            {/if}
                                        </div>
                                    </div>
                                {/if}

                                <!-- Job Description -->
                                <div>
                                    <h4
                                        class="text-sm font-bold uppercase tracking-wider text-[#64748B] mb-3"
                                    >
                                        Job Description
                                    </h4>
                                    <p
                                        class="text-[#334155] bg-[#F8FAFC] rounded-lg p-4 border border-[#E2E8F0] leading-relaxed"
                                    >
                                        {app.job_description}
                                    </p>
                                </div>

                                <!-- Requirements -->
                                {#if app.requirements && app.requirements.length > 0}
                                    <div>
                                        <h4
                                            class="text-sm font-bold uppercase tracking-wider text-[#64748B] mb-3"
                                        >
                                            Requirements
                                        </h4>
                                        <div class="flex flex-wrap gap-2">
                                            {#each app.requirements as req}
                                                <span
                                                    class="px-3 py-1 bg-[#0369A1]/10 text-[#0369A1] rounded-full text-sm font-medium"
                                                >
                                                    {req}
                                                </span>
                                            {/each}
                                        </div>
                                    </div>
                                {/if}

                                <!-- Job URL -->
                                <div class="pt-4">
                                    <a
                                        href={app.job_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        class="inline-flex items-center gap-2 text-[#0369A1] hover:text-[#0284C7] font-semibold transition-colors"
                                        on:click|stopPropagation
                                    >
                                        View Original Job Posting
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            class="h-4 w-4"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                        >
                                            <path
                                                stroke-linecap="round"
                                                stroke-linejoin="round"
                                                stroke-width="2"
                                                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                            />
                                        </svg>
                                    </a>
                                </div>
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</div>

<style>
    /* Smooth transitions */
    * {
        transition:
            background-color 200ms,
            color 200ms,
            transform 200ms;
    }
</style>
