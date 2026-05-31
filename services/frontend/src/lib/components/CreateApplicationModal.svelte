<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import {
		createApplication,
		updateApplication,
		checkDuplicateApplication,
		type CreateApplicationRequest,
		type DuplicateCheckResponse
	} from '$lib/api';
	import { fade, scale } from 'svelte/transition';

	export let isOpen = false;

	const dispatch = createEventDispatcher();

	let job_title = '';
	let company = '';
	let job_url = '';
	let status = 'applied';
	let notes = '';
	let cover_letter_body = '';

	let isSaving = false;
	let isUpdating = false;
	let error = '';

	let duplicateCheck: DuplicateCheckResponse | null = null;
	let showDuplicateWarning = false;

	$: if (job_url) {
		duplicateCheck = null;
		showDuplicateWarning = false;
	}

	async function handleSubmit() {
		if (!job_title || !company) {
			error = 'Job Title and Company are required.';
			return;
		}

		isSaving = true;
		error = '';

		if (job_url) {
			console.log('[duplicate] checking:', job_url);
			try {
				const result = await checkDuplicateApplication(job_url);
				console.log('[duplicate] result:', result);
				if (result.is_duplicate) {
					duplicateCheck = result;
					showDuplicateWarning = true;
					isSaving = false;
					return;
				}
			} catch (e: any) {
				console.error('[duplicate] error:', e);
				error = e.message || 'Failed to check for duplicate';
				isSaving = false;
				return;
			}
		}

		try {
			const data: CreateApplicationRequest = { job_title, company, job_url, status, notes, cover_letter_body };
			await createApplication(data);
			dispatch('success');
			close();
		} catch (e: any) {
			error = e.message || 'Failed to create application';
		} finally {
			isSaving = false;
		}
	}

	async function handleUpdateExisting() {
		if (!duplicateCheck?.existing_application) return;
		const existing = duplicateCheck.existing_application;
		isUpdating = true;
		error = '';
		try {
			const updateData: Record<string, any> = {};
			if (job_title && job_title !== existing.job_title) updateData.job_title = job_title;
			if (company && company !== existing.company) updateData.company = company;
			if (status !== existing.status) updateData.status = status;
			if (notes !== (existing.notes || '')) updateData.notes = notes;
			if (cover_letter_body && cover_letter_body !== (existing.cover_letter_body || '')) updateData.cover_letter_body = cover_letter_body;
			await updateApplication(existing.id, updateData);
			dispatch('success');
			close();
		} catch (e: any) {
			error = e.message || 'Failed to update application';
		} finally {
			isUpdating = false;
		}
	}

	function handleForceCreate() {
		showDuplicateWarning = false;
		duplicateCheck = null;
		isSaving = true;
		error = '';
		const data: CreateApplicationRequest = { job_title, company, job_url, status, notes, cover_letter_body };
		createApplication(data).then(() => { dispatch('success'); close(); }).catch((e: any) => { error = e.message || 'Failed to create application'; }).finally(() => { isSaving = false; });
	}

	function handleCancelDuplicate() {
		showDuplicateWarning = false;
		duplicateCheck = null;
	}

	function close() {
		isOpen = false;
		error = '';
		job_title = '';
		company = '';
		job_url = '';
		status = 'applied';
		notes = '';
		cover_letter_body = '';
		duplicateCheck = null;
		showDuplicateWarning = false;
		dispatch('close');
	}

	function formatDate(isoString: string): string {
		return new Date(isoString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
	}
</script>

{#if isOpen}
<div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm" transition:fade={{ duration: 200 }} on:click|self={close} on:keydown={(e) => e.key === 'Escape' && close()} role="button" tabindex="-1">
<div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]" transition:scale={{ duration: 200, start: 0.95 }}>
<div class="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
<div><h2 class="text-xl font-bold text-slate-900">New Application</h2><p class="text-sm text-slate-500">Add a job application manually to your dashboard.</p></div>
<button on:click={close} class="p-2 hover:bg-slate-200 rounded-full transition-colors text-slate-400"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
</div>
<div class="p-6 overflow-y-auto space-y-6">
{#if error}
<div class="p-4 bg-red-50 border border-red-100 text-red-600 rounded-xl text-sm flex items-start gap-3">
<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mt-0.5 shrink-0" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
<span>{error}</span>
</div>
{/if}
{#if showDuplicateWarning && duplicateCheck?.existing_application}
{@const existing = duplicateCheck.existing_application}
<div class="p-5 bg-amber-50 border border-amber-200 rounded-xl" transition:fade={{ duration: 200 }}>
<div class="flex items-start gap-3 mb-4">
<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-amber-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
<div><h3 class="font-bold text-amber-900 text-base">You already have an application for this job posting</h3><p class="text-sm text-amber-700 mt-1">The URL you entered matches an existing application.</p></div>
</div>
<div class="bg-white rounded-lg border border-amber-200 p-4 mb-4 space-y-2">
<div class="flex items-center justify-between"><div><span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Existing Application</span></div>
<span class="text-xs font-bold px-2 py-1 rounded-full capitalize {existing.status === 'applied' ? 'bg-blue-100 text-blue-700' : existing.status === 'interview' ? 'bg-green-100 text-green-700' : existing.status === 'waiting' ? 'bg-yellow-100 text-yellow-700' : existing.status === 'accepted' ? 'bg-emerald-100 text-emerald-700' : existing.status === 'refused' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}">{existing.status}</span></div>
<p class="font-bold text-slate-900">{existing.job_title}</p><p class="text-sm text-slate-500">{existing.company}</p>
<p class="text-xs text-slate-400">Created {formatDate(existing.created_at)}</p>
</div>
<div class="flex flex-wrap gap-3">
<button on:click={handleUpdateExisting} disabled={isUpdating} class="bg-[#0369A1] hover:bg-[#0284C7] text-white px-6 py-2.5 rounded-xl font-bold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:shadow-none flex items-center gap-2">
{#if isUpdating}<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>Updating...{:else}Update Existing{/if}</button>
<button on:click={handleForceCreate} disabled={isSaving} class="px-6 py-2.5 rounded-xl font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors">Create New Anyway</button>
<button on:click={handleCancelDuplicate} class="px-6 py-2.5 rounded-xl font-semibold text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors">Cancel</button>
</div></div>
{:else}
<div class="grid grid-cols-1 md:grid-cols-2 gap-5">
<div class="space-y-1.5"><label for="company" class="text-sm font-semibold text-slate-700 ml-1">Company *</label><input id="company" type="text" bind:value={company} placeholder="e.g. Google" class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all placeholder:text-slate-400 shadow-sm"/></div>
<div class="space-y-1.5"><label for="job_title" class="text-sm font-semibold text-slate-700 ml-1">Job Title *</label><input id="job_title" type="text" bind:value={job_title} placeholder="e.g. Senior Software Engineer" class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all placeholder:text-slate-400 shadow-sm"/></div>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-5">
<div class="space-y-1.5"><label for="job_url" class="text-sm font-semibold text-slate-700 ml-1">Job URL</label><input id="job_url" type="url" bind:value={job_url} placeholder="https://..." class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all placeholder:text-slate-400 shadow-sm"/></div>
<div class="space-y-1.5"><label for="status" class="text-sm font-semibold text-slate-700 ml-1">Initial Status</label>
<div class="relative">
<select id="status" bind:value={status} class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all appearance-none bg-white shadow-sm">
<option value="applied">Applied</option><option value="waiting">Waiting</option><option value="interview">Interview</option><option value="accepted">Accepted</option><option value="refused">Refused</option><option value="finish">Finished</option></select>
<div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400"><svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/></svg></div>
</div></div></div>
<div class="space-y-1.5"><label for="notes" class="text-sm font-semibold text-slate-700 ml-1">Notes (Internal)</label><textarea id="notes" bind:value={notes} rows="3" placeholder="Key points about this role..." class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all resize-none placeholder:text-slate-400 shadow-sm"></textarea></div>
<div class="space-y-1.5"><label for="cover_letter" class="text-sm font-semibold text-slate-700 ml-1">Cover Letter Body</label><textarea id="cover_letter" bind:value={cover_letter_body} rows="6" placeholder="Paste the cover letter you sent..." class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-[#0369A1] focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all resize-none placeholder:text-slate-400 font-mono text-sm shadow-sm"></textarea></div>
{/if}</div>
<div class="px-6 py-5 border-t border-slate-100 flex items-center justify-end gap-3 bg-slate-50/50">
<button on:click={close} class="px-6 py-2.5 rounded-xl font-semibold text-slate-600 hover:bg-slate-100 transition-colors">Cancel</button>
{#if !showDuplicateWarning}
<button on:click={handleSubmit} disabled={isSaving || !job_title || !company} class="bg-[#0369A1] hover:bg-[#0284C7] text-white px-8 py-2.5 rounded-xl font-bold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:shadow-none flex items-center gap-2">
{#if isSaving}<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>Checking...{:else}Create Application{/if}</button>
{/if}</div></div></div>
{/if}
<style>select{-webkit-appearance:none;-moz-appearance:none;appearance:none}</style>