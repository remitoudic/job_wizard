<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { 
        fetchApplicationDetails, 
        updateApplication, 
        fetchApplicationHistory,
        generatePdf,
        type ApplicationDetails,
        type UpdateApplicationRequest,
        type ApplicationStatusHistory
    } from "$lib/api";
    import { auth } from "../../../stores/auth";
    import { API_URL } from "$lib/api";

    const applicationId = parseInt($page.params.id || "0");
    
    let details: ApplicationDetails | null = null;
    let history: ApplicationStatusHistory[] = [];
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
    let isPdfGenerating = false;
    let pdfUrl = "";

    let isInitialized = false;
    let autoSaveTimeout: ReturnType<typeof setTimeout>;

    onMount(async () => {
        if (!$auth.token) {
            goto("/login");
            return;
        }

        try {
            const [detailsData, historyData] = await Promise.all([
                fetchApplicationDetails(applicationId),
                fetchApplicationHistory(applicationId)
            ]);
            
            details = detailsData;
            history = historyData;
            
            // Initialize editable fields
            editableTitle = details.job_title || "";
            editableCompany = details.company || "";
            editableStatus = details.status || "";
            editableNotes = details.notes || "";
            editableLetterBody = details.cover_letter_final?.body || "";
            
            // Set initialized after values are set to avoid immediate auto-save
            setTimeout(() => { isInitialized = true; }, 500);
        } catch (e: any) {
            error = e.message || "Failed to load application details";
        } finally {
            isLoading = false;
        }
    });

    async function handleSave(showNotification = true) {
        if (!details) return;
        isSaving = true;
        if (showNotification) saveMessage = "";
        
        try {
            const statusChanged = editableStatus !== details.status;

            const updateData: UpdateApplicationRequest = {
                job_title: editableTitle,
                company: editableCompany,
                status: editableStatus,
                notes: editableNotes,
                cover_letter_body: editableLetterBody
            };
            
            await updateApplication(applicationId, updateData);
            
            // Update details to match current state
            details = {
                ...details,
                job_title: editableTitle,
                company: editableCompany,
                status: editableStatus,
                notes: editableNotes,
                cover_letter_final: { ...details.cover_letter_final, body: editableLetterBody }
            };

            // If status changed, refresh history
            if (statusChanged) {
                history = await fetchApplicationHistory(applicationId);
            }

            if (showNotification) {
                saveMessage = "Changes saved successfully!";
                setTimeout(() => { saveMessage = ""; }, 3000);
            }
        } catch (e: any) {
            if (showNotification) {
                error = e.message || "Failed to save changes";
            } else {
                console.error("Auto-save failed:", e);
            }
        } finally {
            isSaving = false;
        }
    }

    function triggerAutoSave() {
        if (!isInitialized) return;
        
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = setTimeout(() => {
            if (!isSaving) {
                handleSave(false); // Background save without full notification
            } else {
                // If already saving, retry in 1s
                triggerAutoSave();
            }
        }, 2000);
    }

    // Reactive watcher for auto-save
    $: {
        if (isInitialized && details) {
            const changed = 
                editableTitle !== (details.job_title || "") ||
                editableCompany !== (details.company || "") ||
                editableStatus !== (details.status || "") ||
                editableNotes !== (details.notes || "") ||
                editableLetterBody !== (details.cover_letter_final?.body || "");
            
            if (changed) {
                triggerAutoSave();
            }
        }
    }

    function formatDate(dateStr: string) {
        const date = new Date(dateStr);
        return date.toLocaleDateString(undefined, { 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function getStatusColor(status: string) {
        const colors: Record<string, string> = {
            applied: 'bg-blue-100 text-blue-700',
            waiting: 'bg-amber-100 text-amber-700',
            interview: 'bg-purple-100 text-purple-700',
            refused: 'bg-red-100 text-red-700',
            accepted: 'bg-green-100 text-green-700',
            finish: 'bg-slate-100 text-slate-700'
        };
        return colors[status.toLowerCase()] || 'bg-slate-100 text-slate-700';
    }

    async function handleGeneratePdf() {
        if (!editableLetterBody || !details) return;

        isPdfGenerating = true;
        error = "";

        try {
            const result = await generatePdf({
                cover_letter: editableLetterBody,
                job_title: editableTitle,
                company: editableCompany,
                user_name: ($auth.user?.first_name && $auth.user?.surname) 
                    ? `${$auth.user.first_name} ${$auth.user.surname}` 
                    : ($auth.user?.email || "Applicant"),
                first_name: $auth.user?.first_name || "",
                surname: $auth.user?.surname || "",
                email: $auth.user?.email || "",
                phone: $auth.user?.phone || "",
                linkedin: $auth.user?.linkedin_url || "",
                template_name: "british", // Default
                full_name: ($auth.user?.first_name && $auth.user?.surname) 
                    ? `${$auth.user.first_name} ${$auth.user.surname}` 
                    : "",
                address_street: $auth.user?.street || "",
                address_postcode: $auth.user?.postcode || "",
                address_city: $auth.user?.city || "",
                address_country: $auth.user?.country || "",
            });

            pdfUrl = result.url;
            handleDownload();
        } catch (e: any) {
            error = e.message || "Failed to generate PDF";
        } finally {
            isPdfGenerating = false;
        }
    }

    async function handleDownload() {
        if (!pdfUrl) return;

        const fullUrl = pdfUrl.startsWith("http") 
            ? pdfUrl 
            : `${API_URL}${pdfUrl}`;

        try {
            const headers: Record<string, string> = {};
            if ($auth.token) {
                headers['Authorization'] = `Bearer ${$auth.token}`;
            }

            const response = await fetch(fullUrl, {
                headers,
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }

            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);

            const link = document.createElement("a");
            link.href = blobUrl;
            
            const companyName = editableCompany.replace(/[^a-zA-Z0-9]/g, "_");
            const date = new Date().toISOString().split("T")[0];
            link.download = `Cover_Letter_${companyName}_${date}.pdf`;
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(blobUrl);
        } catch (e) {
            console.error("Download failed:", e);
            window.open(fullUrl, "_blank");
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
                    on:click={handleGeneratePdf}
                    disabled={isPdfGenerating || isLoading}
                    class="bg-white border border-[#E2E8F0] text-slate-700 px-4 py-2 rounded-lg font-semibold transition-all shadow-sm hover:shadow-md disabled:opacity-50 flex items-center gap-2"
                >
                    {#if isPdfGenerating}
                        <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                        Generating...
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Download PDF
                    {/if}
                </button>

                <button 
                    on:click={() => handleSave()}
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
                            <span class="text-xs text-slate-400">Autosave enabled - Changes are saved automatically</span>
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

                            <div class="pt-2">
                                <a 
                                    href={details.job_url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    class="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2 group transition-colors"
                                >
                                    <span>View Original Job Posting</span>
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transform group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                    </svg>
                                </a>
                            </div>
                        </div>
                    </section>

                    <!-- Status History Timeline -->
                    <section class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
                        <h2 class="text-sm font-bold uppercase tracking-wider text-slate-500">Status History</h2>
                        <div class="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-100">
                            {#each history as item}
                                <div class="relative">
                                    <!-- Dot -->
                                    <div class="absolute -left-[20px] top-1.5 w-3 h-3 rounded-full border-2 border-white bg-blue-500 shadow-sm z-10"></div>
                                    
                                    <div class="flex flex-col">
                                        <div class="flex items-center gap-2">
                                            {#if item.old_status}
                                                <span class="text-xs text-slate-400">{item.old_status}</span>
                                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                                </svg>
                                            {/if}
                                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase {getStatusColor(item.new_status)}">
                                                {item.new_status}
                                            </span>
                                        </div>
                                        <span class="text-[10px] text-slate-400 mt-1">{formatDate(item.created_at)}</span>
                                        {#if item.notes}
                                            <p class="text-xs text-slate-600 mt-1 italic italic-slate-500">"{item.notes}"</p>
                                        {/if}
                                    </div>
                                </div>
                            {:else}
                                <p class="text-xs text-slate-400 italic">No history recorded yet.</p>
                            {/each}
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
