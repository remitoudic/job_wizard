<script lang="ts">
    import { onMount } from "svelte";
    import {
        fetchUserApplications,
        updateApplicationStatus,
        deleteApplication,
        type ApplicationListItem,
    } from "$lib/api";
    import { auth } from "../../stores/auth";
    import { goto } from "$app/navigation";

    // SvelteKit may pass `data` and `params` to pages — declare to prevent runtime warnings
    export let data: any = {};
    export let params: Record<string, string> = {};

    let applications: ApplicationListItem[] = [];
    let isLoading = true;
    let error = "";
    let expandedId: number | null = null;
    let viewMode: "list" | "kanban" = "list";
    let draggedAppId: number | null = null;

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

    function handleDelete(id: number) {
        if (
            !confirm(
                "Are you sure you want to delete this application? This action cannot be undone.",
            )
        ) {
            return;
        }

        // Optimistic update
        const originalApplications = [...applications];
        applications = applications.filter((app) => app.id !== id);

        deleteApplication(id).catch((e) => {
            console.error("Failed to delete application:", e);
            // Revert on failure
            applications = originalApplications;
            error = "Failed to delete application. Please try again.";
            setTimeout(() => (error = ""), 3000);
        });
    }

    async function handleStatusChange(id: number, newStatus: string) {
        // Optimistic update
        const originalApplications = [...applications];
        applications = applications.map((app) =>
            app.id === id ? { ...app, status: newStatus } : app,
        );

        try {
            await updateApplicationStatus(id, newStatus);
        } catch (e) {
            console.error("Failed to update status:", e);
            // Revert on failure
            applications = originalApplications;
            error = "Failed to update status. Please try again.";
            // Clear error after 3 seconds
            setTimeout(() => (error = ""), 3000);
        }
    }

    function handleDragStart(e: DragEvent, id: number) {
        draggedAppId = id;
        if (e.dataTransfer) {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', id.toString());
        }
    }

    function handleDragEnd() {
        draggedAppId = null;
    }

    function handleDrop(e: DragEvent, columnId: string) {
        e.preventDefault();
        if (!draggedAppId) return;

        let newStatus = columnId;
        if (columnId === 'done') {
            newStatus = 'finish';
        }

        const app = applications.find(a => a.id === draggedAppId);
        // Only update if status actually changes (ignoring different done states for now)
        if (app && app.status !== newStatus && !(columnId === 'done' && ['finish', 'accepted', 'refused'].includes(app.status))) {
            handleStatusChange(draggedAppId, newStatus);
        }
        draggedAppId = null;
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

    $: kanbanColumns = [
        { id: 'applied', title: 'Applied', apps: applications.filter(a => a.status === 'applied') },
        { id: 'interview', title: 'Interview', apps: applications.filter(a => a.status === 'interview') },
        { id: 'waiting', title: 'Waiting', apps: applications.filter(a => a.status === 'waiting') },
        { id: 'done', title: 'Done', apps: applications.filter(a => ['finish', 'accepted', 'refused'].includes(a.status)) }
    ];
</script>

<svelte:head>
    <title>My Applications - Vite a Job</title>
</svelte:head>

<div class="min-h-screen py-16 px-4 bg-gradient-to-b from-white to-slate-50">
    <div class="mx-auto transition-all duration-300 {viewMode === 'kanban' ? 'max-w-7xl' : 'max-w-4xl'}">
        <!-- Header -->
        <div class="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
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
                    <span class="font-semibold">Back to Vite a Job</span>
                </a>
                <h1 class="text-4xl font-extrabold text-[#0F172A] mb-2">
                    My Applications
                </h1>
                <p class="text-[#334155]">
                    Track your job applications and cover letters
                </p>
            </div>
            
            <!-- View Toggle -->
            {#if !isLoading && !error && applications.length > 0}
                <div class="flex items-center gap-2 bg-white p-1 rounded-lg border border-[#E2E8F0] shadow-sm self-start md:self-auto">
                    <button 
                        class="px-4 py-2 rounded-md text-sm font-semibold transition-all {viewMode === 'list' ? 'bg-[#0369A1] text-white shadow' : 'text-[#64748B] hover:text-[#0F172A]'}"
                        on:click={() => viewMode = 'list'}
                    >
                        List
                    </button>
                    <button 
                        class="px-4 py-2 rounded-md text-sm font-semibold transition-all {viewMode === 'kanban' ? 'bg-[#0369A1] text-white shadow' : 'text-[#64748B] hover:text-[#0F172A]'}"
                        on:click={() => viewMode = 'kanban'}
                    >
                        Kanban
                    </button>
                </div>
            {/if}
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
                    Start applying to jobs with Vite a Job to see them here
                </p>
            </div>
        {/if}

        <!-- Views -->
        {#if !isLoading && !error && applications.length > 0}
            {#if viewMode === 'list'}
            <div
                class="bg-white rounded-lg border border-[#E2E8F0] shadow-sm overflow-hidden"
            >
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-slate-50 border-b border-slate-200">
                                <th
                                    class="p-4 font-semibold text-slate-600 text-sm whitespace-nowrap"
                                    >Date</th
                                >
                                <th
                                    class="p-4 font-semibold text-slate-600 text-sm"
                                    >Company</th
                                >
                                <th
                                    class="p-4 font-semibold text-slate-600 text-sm"
                                    >Status</th
                                >
                                <th
                                    class="p-4 font-semibold text-slate-600 text-sm text-right"
                                    >Actions</th
                                >
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            {#each applications as app (app.id)}
                                <!-- Main Row -->
                                <tr
                                    class="hover:bg-slate-50 transition-colors cursor-pointer"
                                    on:click={() => toggleExpand(app.id)}
                                >
                                    <td
                                        class="p-4 text-slate-600 whitespace-nowrap align-top"
                                    >
                                        {formatDate(app.created_at)}
                                    </td>
                                    <td class="p-4 align-top">
                                        <div class="font-bold text-slate-900">
                                            {app.company}
                                        </div>
                                        <div class="text-sm text-slate-500">
                                            {app.job_title}
                                        </div>
                                    </td>
                                    <td
                                        class="p-4 align-top"
                                        on:click|stopPropagation
                                    >
                                        <div
                                            class="relative group inline-block"
                                        >
                                            <select
                                                class="appearance-none pl-3 pr-8 py-1 rounded-full text-xs font-semibold uppercase cursor-pointer border-0 outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 transition-all {getStatusColor(
                                                    app.status,
                                                )}"
                                                value={app.status}
                                                on:change={(e) =>
                                                    handleStatusChange(
                                                        app.id,
                                                        e.currentTarget.value,
                                                    )}
                                            >
                                                <option value="applied"
                                                    >Applied</option
                                                >
                                                <option value="waiting"
                                                    >Waiting</option
                                                >
                                                <option value="interview"
                                                    >Interview</option
                                                >
                                                <option value="refused"
                                                    >Refused</option
                                                >
                                                <option value="accepted"
                                                    >Accepted</option
                                                >
                                                <option value="finish"
                                                    >Finish</option
                                                >
                                            </select>
                                            <div
                                                class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2"
                                            >
                                                <svg
                                                    class="h-3 w-3 opacity-60"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    viewBox="0 0 24 24"
                                                >
                                                    <path
                                                        stroke-linecap="round"
                                                        stroke-linejoin="round"
                                                        stroke-width="3"
                                                        d="M19 9l-7 7-7-7"
                                                    />
                                                </svg>
                                            </div>
                                        </div>
                                    </td>
                                    <td class="p-4 align-top text-right">
                                        <div
                                            class="flex items-center justify-end gap-3 transition-transform duration-200"
                                        >
                                            <button
                                                class="text-slate-400 hover:text-red-500 transition-colors p-1"
                                                on:click|stopPropagation={() =>
                                                    handleDelete(app.id)}
                                                title="Delete Application"
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
                                                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                                    />
                                                </svg>
                                            </button>
                                            <div
                                                class="transition-transform duration-200 {expandedId ===
                                                app.id
                                                    ? 'rotate-180'
                                                    : ''}"
                                            >
                                                <svg
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    class="h-5 w-5 text-slate-400"
                                                    viewBox="0 0 20 20"
                                                    fill="currentColor"
                                                >
                                                    <path
                                                        fill-rule="evenodd"
                                                        d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                                                        clip-rule="evenodd"
                                                    />
                                                </svg>
                                            </div>
                                        </div>
                                    </td>
                                </tr>

                                <!-- Expanded Row -->
                                {#if expandedId === app.id}
                                    <tr class="bg-slate-50/50">
                                        <td
                                            colspan="4"
                                            class="p-0 border-b border-slate-100"
                                        >
                                            <div class="p-6 space-y-6">
                                                <!-- Cover Letter -->
                                                <div>
                                                    <h4
                                                        class="text-sm font-bold uppercase tracking-wider text-[#64748B] mb-3"
                                                    >
                                                        Cover Letter
                                                    </h4>
                                                    <div
                                                        class="bg-white rounded-lg p-4 border border-[#E2E8F0]"
                                                    >
                                                        <p
                                                            class="text-[#334155] whitespace-pre-wrap leading-relaxed"
                                                        >
                                                            {app
                                                                .cover_letter_final
                                                                .body ||
                                                                "No cover letter body available"}
                                                        </p>
                                                    </div>
                                                </div>

                                                <!-- Contact Info Grid -->
                                                {#if app.header && Object.keys(app.header).length > 0}
                                                    <div>
                                                        <h4
                                                            class="text-sm font-bold uppercase tracking-wider text-[#64748B] mb-3"
                                                        >
                                                            Contact Information
                                                        </h4>
                                                        <div
                                                            class="grid grid-cols-1 md:grid-cols-2 gap-3 bg-white rounded-lg p-4 border border-[#E2E8F0]"
                                                        >
                                                            {#each Object.entries(app.header) as [key, value]}
                                                                {#if value}
                                                                    <div>
                                                                        <span
                                                                            class="text-xs font-semibold text-[#64748B] uppercase"
                                                                            >{key}:</span
                                                                        >
                                                                        <p
                                                                            class="text-[#0F172A]"
                                                                        >
                                                                            {value}
                                                                        </p>
                                                                    </div>
                                                                {/if}
                                                            {/each}
                                                        </div>
                                                    </div>
                                                {/if}

                                                <!-- Job Info & Requirements -->
                                                <div
                                                    class="grid grid-cols-1 md:grid-cols-2 gap-6"
                                                >
                                                    <div>
                                                        <h4
                                                            class="text-sm font-bold uppercase tracking-wider text-[#64748B] mb-3"
                                                        >
                                                            Job Description
                                                        </h4>
                                                        <div
                                                            class="bg-white rounded-lg p-4 border border-[#E2E8F0] max-h-60 overflow-y-auto text-sm text-[#334155]"
                                                        >
                                                            {app.job_description}
                                                        </div>
                                                    </div>

                                                    {#if app.requirements?.length}
                                                        <div>
                                                            <h4
                                                                class="text-sm font-bold uppercase tracking-wider text-[#64748B] mb-3"
                                                            >
                                                                Requirements
                                                            </h4>
                                                            <div
                                                                class="flex flex-wrap gap-2"
                                                            >
                                                                {#each app.requirements as req}
                                                                    <span
                                                                        class="px-2 py-1 bg-white border border-slate-200 rounded text-xs text-slate-600"
                                                                    >
                                                                        {req}
                                                                    </span>
                                                                {/each}
                                                            </div>
                                                        </div>
                                                    {/if}
                                                </div>

                                                <!-- Link -->
                                                <div class="pt-2">
                                                    <a
                                                        href={app.job_url}
                                                        target="_blank"
                                                        class="text-sm text-[#0369A1] hover:underline font-medium inline-flex items-center gap-1"
                                                    >
                                                        View Original Job
                                                        Posting
                                                        <svg
                                                            xmlns="http://www.w3.org/2000/svg"
                                                            class="h-3 w-3"
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
                                        </td>
                                    </tr>
                                {/if}
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>
            {:else}
            <!-- Kanban View -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-start">
                {#each kanbanColumns as column}
                    <div class="bg-slate-100/50 rounded-xl p-4 border border-slate-200 transition-colors"
                         role="list"
                         on:dragover|preventDefault
                         on:drop={(e) => handleDrop(e, column.id)}>
                        <div class="flex items-center justify-between mb-4 px-1">
                            <h3 class="font-bold text-slate-800">{column.title}</h3>
                            <span class="bg-white text-slate-500 text-xs font-bold px-2.5 py-1 rounded-full border border-slate-200 shadow-sm">{column.apps.length}</span>
                        </div>
                        <div class="flex flex-col gap-3">
                            {#each column.apps as app (app.id)}
                                <div class="bg-white border border-slate-200 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 {draggedAppId === app.id ? 'opacity-50 scale-95 ring-2 ring-[#0369A1] shadow-lg' : ''}"
                                     role="listitem"
                                     draggable="true"
                                     on:dragstart={(e) => handleDragStart(e, app.id)}
                                     on:dragend={handleDragEnd}>
                                    <div class="p-4 cursor-pointer" role="button" tabindex="0" on:click={() => toggleExpand(app.id)} on:keydown={(e) => e.key === 'Enter' && toggleExpand(app.id)}>
                                        <!-- Card Header -->
                                        <div class="flex justify-between items-start mb-2 gap-2">
                                            <div>
                                                <h4 class="font-bold text-slate-900 leading-tight">{app.company}</h4>
                                                <p class="text-xs text-slate-500 mt-0.5">{formatDate(app.created_at)}</p>
                                            </div>
                                            <div class="relative group" on:click|stopPropagation>
                                                <select
                                                    class="appearance-none pl-3 pr-8 py-1 rounded-full text-[10px] font-bold uppercase cursor-pointer border-0 outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 transition-all {getStatusColor(app.status)}"
                                                    value={app.status}
                                                    on:change={(e) => handleStatusChange(app.id, e.currentTarget.value)}
                                                >
                                                    <option value="applied">Applied</option>
                                                    <option value="waiting">Waiting</option>
                                                    <option value="interview">Interview</option>
                                                    <option value="refused">Refused</option>
                                                    <option value="accepted">Accepted</option>
                                                    <option value="finish">Finish</option>
                                                </select>
                                                <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2">
                                                    <svg class="h-3 w-3 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 9l-7 7-7-7" />
                                                    </svg>
                                                </div>
                                            </div>
                                        </div>
                                        <!-- Job Title -->
                                        <div class="text-sm text-slate-600 font-medium mb-3">
                                            {app.job_title}
                                        </div>
                                        
                                        <!-- Card Actions -->
                                        <div class="flex items-center justify-between pt-3 border-t border-slate-100">
                                            <button
                                                class="text-slate-400 hover:text-red-500 transition-colors p-1 -ml-1"
                                                on:click|stopPropagation={() => handleDelete(app.id)}
                                                title="Delete Application"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                            <div class="flex items-center gap-1 text-xs font-semibold text-slate-500">
                                                <span>Details</span>
                                                <div class="transition-transform duration-200 {expandedId === app.id ? 'rotate-180' : ''}">
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                                        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                                                    </svg>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- Expanded Content -->
                                    {#if expandedId === app.id}
                                        <div class="bg-slate-50 border-t border-slate-200 p-4 rounded-b-lg space-y-4">
                                            <!-- Cover Letter -->
                                            <div>
                                                <h4 class="text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2">Cover Letter</h4>
                                                <div class="bg-white rounded p-3 border border-[#E2E8F0]">
                                                    <p class="text-xs text-[#334155] whitespace-pre-wrap leading-relaxed line-clamp-4 hover:line-clamp-none transition-all">
                                                        {app.cover_letter_final.body || "No cover letter body available"}
                                                    </p>
                                                </div>
                                            </div>
                                            <!-- Contact Info Grid -->
                                            {#if app.header && Object.keys(app.header).length > 0}
                                                <div>
                                                    <h4 class="text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2">Contact</h4>
                                                    <div class="grid grid-cols-1 gap-2 bg-white rounded p-3 border border-[#E2E8F0]">
                                                        {#each Object.entries(app.header) as [key, value]}
                                                            {#if value}
                                                                <div>
                                                                    <span class="text-[10px] font-semibold text-[#64748B] uppercase">{key}:</span>
                                                                    <p class="text-xs text-[#0F172A] break-all">{value}</p>
                                                                </div>
                                                            {/if}
                                                        {/each}
                                                    </div>
                                                </div>
                                            {/if}
                                            <div class="pt-2 flex justify-between items-center border-t border-slate-200">
                                                <a href={app.job_url} target="_blank" class="text-xs text-[#0369A1] hover:underline font-medium inline-flex items-center gap-1">
                                                    Original Job
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                                    </svg>
                                                </a>
                                            </div>
                                        </div>
                                    {/if}
                                </div>
                            {/each}
                            {#if column.apps.length === 0}
                                <div class="py-8 border-2 border-dashed border-slate-200 rounded-lg flex items-center justify-center">
                                    <span class="text-sm font-medium text-slate-400">No applications</span>
                                </div>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
            {/if}
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
