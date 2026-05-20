<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let activeCVName: string | null = null;
	export let contextSnippet: string | null = null;
	export let isAuthenticated: boolean = false;

	let showSnippet = false;
	const dispatch = createEventDispatcher();
</script>

<div class="space-y-3">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-2">
			<span class="text-xs font-bold uppercase tracking-wider text-[#64748B]">
				Source of Truth
			</span>
			{#if activeCVName}
				<div
					class="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-100 text-[10px] font-bold text-emerald-600 uppercase tracking-tight antialiased"
				>
					<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
					Ready
				</div>
			{/if}
		</div>

		{#if activeCVName && contextSnippet}
			<button
				on:click={() => (showSnippet = !showSnippet)}
				class="text-[10px] font-bold uppercase tracking-widest text-[#0369A1] hover:text-[#075985] transition-colors focus:outline-none"
			>
				{showSnippet ? 'Hide' : 'View'} Context
			</button>
		{/if}
	</div>

	{#if activeCVName}
		<div
			class="p-3 rounded-lg border border-[#E2E8F0] bg-white flex items-center justify-between group hover:border-[#0369A1]/30 transition-all"
		>
			<div class="flex items-center gap-3 overflow-hidden">
				<div
					class="p-2 rounded-md bg-[#F8FAFC] text-[#64748B] group-hover:bg-[#F0F9FF] group-hover:text-[#0369A1] transition-colors"
				>
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
							d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
						/>
					</svg>
				</div>
				<div class="overflow-hidden">
					<div class="text-xs font-semibold text-[#0F172A] truncate">
						{activeCVName}
					</div>
					<div class="text-[10px] text-[#64748B]">Active User CV • Linked to Profile</div>
				</div>
			</div>

			<a
				href="/profile"
				class="opacity-0 group-hover:opacity-100 p-1.5 rounded-md hover:bg-[#F1F5F9] text-[#64748B] transition-all"
				title="Manage CVs in Profile"
			>
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
						d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
					/>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
					/>
				</svg>
			</a>
		</div>
	{:else if !isAuthenticated}
		<div class="p-3 rounded-lg border border-dashed border-[#E2E8F0] bg-[#F8FAFC] text-center">
			<p class="text-[10px] text-[#64748B]">Log in to automatically use your stored CV data.</p>
		</div>
	{/if}

	{#if showSnippet && contextSnippet}
		<div class="animate-in fade-in slide-in-from-top-2">
			<div class="p-4 rounded-lg bg-[#0F172A] border border-slate-800 shadow-inner overflow-hidden">
				<div class="flex items-center justify-between mb-2">
					<span class="text-[9px] font-mono uppercase tracking-widest text-slate-500"
						>LLM Data Stream (Preview)</span
					>
				</div>
				<div class="max-h-[120px] overflow-y-auto pr-2 custom-scrollbar">
					<p
						class="text-[11px] font-mono text-slate-300 leading-relaxed break-words whitespace-pre-wrap selection:bg-sky-500/30"
					>
						{contextSnippet}
					</p>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.1);
		border-radius: 10px;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb:hover {
		background: rgba(255, 255, 255, 0.2);
	}
</style>
