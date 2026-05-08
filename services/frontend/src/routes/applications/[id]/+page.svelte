<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { 
        fetchApplicationDetails, 
        updateApplication, 
        type ApplicationDetails,
        type UpdateApplicationRequest 
    } from "$lib/api";
    import { auth } from "../../../stores/auth";

    const applicationId = parseInt($page.params.id);
    
    let details: ApplicationDetails | null = null;
    let isLoading = true;
    let isSaving = false;
    let error = "";
    let saveMessage = "";

    // Editable fields
    let editableTitle = "";
    let editableCompany = "";
    let editableStatus = "";
    let editableNotes = "";
    let editableLetterBody = "";

    onMount(async () => {
        if (!$auth.token) {
            goto("/login");
            return;
        }

        try {
            details = await fetchApplicationDetails(applicationId);
            
            // Initialize editable fields
            editableTitle = details.job_title || "";
            editableCompany = details.company || "";
            editableStatus = details.status || "";
            editableNotes = details.notes || "";
            editableLetterBody = details.cover_letter_final?.body || "";
        } catch (e: any) {
            error = e.message || "Failed to load application details";
        } finally {
            isLoading = false;
        }
    });

    async function handleSave() {
        if (!details) return;
        isSaving = true;
        saveMessage = "";
        
        try {
            const updateData: UpdateApplicationRequest = {
                job_title: editableTitle,
                company: editableCompany,
                status: editableStatus,
                notes: editableNotes,
                cover_letter_body: editableLetterBody
            };
            
            await updateApplication(applicationId, updateData);
            saveMessage = "Changes saved successfully!";
            setTimeout(() => { saveMessage = ""; }, 3000);
        } catch (e: any) {
            error = e.message || "Failed to save changes";
        } finally {
            isSaving = false;
        }
    }
</script>

<div class="min-h-screen bg-[#F8FAFC] pb-20">
    <!-- Header -->
    <header class="bg-white border-b border-[#E2E8F0] sticky top-0 z-10 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
            <div class="flex items-center gap-4">
                <button 
                    on:click={() => goto("/applications")}
                    class="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-500"
                    title="Back to Applications"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                </button>
                <div>
                    {#if isLoading}
                        <div class="h-6 w-48 bg-slate-100 animate-pulse rounded"></div>
                    {:else}
                        <h1 class="text-xl font-bold text-slate-900 truncate max-w-md">
                            {editableCompany} - {editableTitle}
                        </h1>
                    {/if}
                </div>
            </div>

            <div class="flex items-center gap-4">
                {#if saveMessage}
                    <span class="text-green-600 text-sm font-medium animate-fade-in">{saveMessage}</span>
                {/if}
                <button 
                    on:click={handleSave}
                    disabled={isSaving || isLoading}
                    class="bg-[#0369A1] hover:bg-[#0284C7] text-white px-6 py-2 rounded-lg font-semibold transition-all shadow-md hover:shadow-lg disabled:opacity-50 flex items-center gap-2"
                >
                    {#if isSaving}
                        <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    {/if}
                    Save Changes
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8">
        {#if isLoading}
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div class="lg:col-span-2 space-y-6">
                    <div class="h-96 bg-white rounded-xl border border-slate-200 animate-pulse"></div>
                </div>
                <div class="space-y-6">
                    <div class="h-64 bg-white rounded-xl border border-slate-200 animate-pulse"></div>
                    <div class="h-64 bg-white rounded-xl border border-slate-200 animate-pulse"></div>
                </div>
            </div>
        {:else if error}
            <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl text-center">
                <p>{error}</p>
                <button on:click={() => window.location.reload()} class="mt-4 text-red-800 font-bold underline">Try Again</button>
            </div>
        {:else if details}
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Left: Cover Letter Editor -->
                <div class="lg:col-span-2 space-y-6">
                    <section class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden flex flex-col h-[calc(100vh-12rem)]">
                        <div class="p-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                            <h2 class="text-sm font-bold uppercase tracking-wider text-slate-500">Cover Letter Body</h2>
                            <span class="text-xs text-slate-400">Autosave disabled - Click Save Changes to persist</span>
                        </div>
                        <textarea 
                            bind:value={editableLetterBody}
                            class="flex-1 p-8 outline-none text-slate-700 leading-relaxed font-serif text-lg resize-none"
                            placeholder="Write your cover letter here..."
                        ></textarea>
                    </section>
                </div>

                <!-- Right: Meta & Job Details -->
                <div class="space-y-6">
                    <!-- Status & Quick Info -->
                    <section class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
                        <h2 class="text-sm font-bold uppercase tracking-wider text-slate-500">Application Info</h2>
                        
                        <div class="space-y-3">
                            <label class="block">
                                <span class="text-xs font-semibold text-slate-500 uppercase">Status</span>
                                <select 
                                    bind:value={editableStatus}
                                    class="w-full mt-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                                >
                                    <option value="applied">Applied</option>
                                    <option value="waiting">Waiting</option>
                                    <option value="interview">Interview</option>
                                    <option value="refused">Refused</option>
                                    <option value="accepted">Accepted</option>
                                    <option value="finish">Finished</option>
                                </select>
                            </label>

                            <label class="block">
                                <span class="text-xs font-semibold text-slate-500 uppercase">Job Title</span>
                                <input 
                                    type="text" 
                                    bind:value={editableTitle}
                                    class="w-full mt-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                                />
                            </label>

                            <label class="block">
                                <span class="text-xs font-semibold text-slate-500 uppercase">Company</span>
                                <input 
                                    type="text" 
                                    bind:value={editableCompany}
                                    class="w-full mt-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                                />
                            </label>
                        </div>
                    </section>

                    <!-- Personal Notes -->
                    <section class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
                        <h2 class="text-sm font-bold uppercase tracking-wider text-slate-500">Personal Notes</h2>
                        <textarea 
                            bind:value={editableNotes}
                            class="w-full min-h-[150px] bg-amber-50/30 border border-amber-100 rounded-lg p-4 text-sm text-slate-700 outline-none focus:ring-2 focus:ring-amber-200 transition-all placeholder:text-slate-400"
                            placeholder="Add interview notes, follow-up dates, or reminders..."
                        ></textarea>
                    </section>

                    <!-- Original Job Description (Read-only) -->
                    <section class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
                        <div class="p-4 bg-slate-50 border-b border-slate-100">
                            <h2 class="text-sm font-bold uppercase tracking-wider text-slate-500">Job Description</h2>
                        </div>
                        <div class="p-6 max-h-60 overflow-y-auto">
                            <p class="text-xs text-slate-600 whitespace-pre-wrap leading-relaxed">
                                {details.job_description}
                            </p>
                        </div>
                    </section>
                </div>
            </div>
        {/if}
    </main>
</div>

<style>
    @keyframes fade-in {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in {
        animation: fade-in 0.3s ease-out forwards;
    }
</style>
