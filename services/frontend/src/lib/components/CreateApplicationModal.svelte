<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { createApplication, type CreateApplicationRequest } from '$lib/api';
    import { fade, scale } from 'svelte/transition';

    export let isOpen = false;

    const dispatch = createEventDispatcher();

    let job_title = "";
    let company = "";
    let job_url = "";
    let status = "applied";
    let notes = "";
    let cover_letter_body = "";

    let isSaving = false;
    let error = "";

    async function handleSubmit() {
        if (!job_title || !company) {
            error = "Job Title and Company are required.";
            return;
        }

        isSaving = true;
        error = "";

        try {
            const data: CreateApplicationRequest = {
                job_title,
                company,
                job_url,
                status,
                notes,
                cover_letter_body
            };

            await createApplication(data);
            dispatch('success');
            close();
        } catch (e: any) {
            error = e.message || "Failed to create application";
        } finally {
            isSaving = false;
        }
    }

    function close() {
        isOpen = false;
        error = "";
        // Reset fields
        job_title = "";
        company = "";
        job_url = "";
        status = "applied";
        notes = "";
        cover_letter_body = "";
        dispatch('close');
    }
</script>

{#if isOpen}
<div 
    class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm"
    transition:fade={{ duration: 200 }}
    on:click|self={close}
    on:keydown={(e) => e.key === 'Escape' && close()}
    role="button"
    tabindex="-1"
>
    <div 
        class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]"
        transition:scale={{ duration: 200, start: 0.95 }}
    >
        <!-- Header -->
        <div class="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <div>
                <h2 class="text-xl font-bold text-slate-900">New Application</h2>
                <p class="text-sm text-slate-500">Add a job application manually to your dashboard.</p>
            </div>
            <button 
                on:click={close}
                class="p-2 hover:bg-slate-200 rounded-full transition-colors text-slate-400"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>

        <!-- Body -->
        <div class="p-6 overflow-y-auto space-y-6">
            {#if error}
                <div class="p-4 bg-red-50 border border-red-100 text-red-600 rounded-xl text-sm flex items-start gap-3">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mt-0.5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                    <span>{error}</span>
                </div>
            {/if}

            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div class="space-y-1.5">
                    <label for="company" class="text-sm font-semibold text-slate-700 ml-1">Company *</label>
                    <input 
                        id="company"
                        type="text" 
                        bind:value={company}
                        placeholder="e.g. Google"
                        class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all placeholder:text-slate-400 shadow-sm"
                    />
                </div>
                <div class="space-y-1.5">
                    <label for="job_title" class="text-sm font-semibold text-slate-700 ml-1">Job Title *</label>
                    <input 
                        id="job_title"
                        type="text" 
                        bind:value={job_title}
                        placeholder="e.g. Senior Software Engineer"
                        class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all placeholder:text-slate-400 shadow-sm"
                    />
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div class="space-y-1.5">
                    <label for="job_url" class="text-sm font-semibold text-slate-700 ml-1">Job URL</label>
                    <input 
                        id="job_url"
                        type="url" 
                        bind:value={job_url}
                        placeholder="https://..."
                        class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all placeholder:text-slate-400 shadow-sm"
                    />
                </div>
                <div class="space-y-1.5">
                    <label for="status" class="text-sm font-semibold text-slate-700 ml-1">Initial Status</label>
                    <div class="relative">
                        <select 
                            id="status"
                            bind:value={status}
                            class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all appearance-none bg-white shadow-sm"
                        >
                            <option value="applied">Applied</option>
                            <option value="waiting">Waiting</option>
                            <option value="interview">Interview</option>
                            <option value="accepted">Accepted</option>
                            <option value="refused">Refused</option>
                            <option value="finish">Finished</option>
                        </select>
                        <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                            </svg>
                        </div>
                    </div>
                </div>
            </div>

            <div class="space-y-1.5">
                <label for="notes" class="text-sm font-semibold text-slate-700 ml-1">Notes (Internal)</label>
                <textarea 
                    id="notes"
                    bind:value={notes}
                    rows="3"
                    placeholder="Key points about this role..."
                    class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all resize-none placeholder:text-slate-400 shadow-sm"
                ></textarea>
            </div>

            <div class="space-y-1.5">
                <label for="cover_letter" class="text-sm font-semibold text-slate-700 ml-1">Cover Letter Body</label>
                <textarea 
                    id="cover_letter"
                    bind:value={cover_letter_body}
                    rows="6"
                    placeholder="Paste the cover letter you sent..."
                    class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all resize-none placeholder:text-slate-400 font-mono text-sm shadow-sm"
                ></textarea>
            </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-5 border-t border-slate-100 flex items-center justify-end gap-3 bg-slate-50/50">
            <button 
                on:click={close}
                class="px-6 py-2.5 rounded-xl font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
                Cancel
            </button>
            <button 
                on:click={handleSubmit}
                disabled={isSaving || !job_title || !company}
                class="bg-[#0369A1] hover:bg-[#0284C7] text-white px-8 py-2.5 rounded-xl font-bold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:shadow-none flex items-center gap-2"
            >
                {#if isSaving}
                    <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating...
                {:else}
                    Create Application
                {/if}
            </button>
        </div>
    </div>
</div>
{/if}

<style>
    /* Custom styles if needed beyond Tailwind */
    select {
        -webkit-appearance: none;
        -moz-appearance: none;
        appearance: none;
    }
</style>
