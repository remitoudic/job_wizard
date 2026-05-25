<script lang="ts">
	import SEO from '$lib/components/SEO.svelte';
	import { fade, fly } from 'svelte/transition';
	import { onMount } from 'svelte';

	let mounted = false;
	onMount(() => {
		mounted = true;
	});
</script>

<SEO
	title="Why Job-Vite? - The 3-Agent AI Crew"
	description="Discover how our multi-agent CrewAI system employs three specialized AI experts—an Analyst, a Copywriter, and an Editor—to generate high-converting, human-grade cover letters."
	canonical="https://job-vite.com/why"
/>

<div class="min-h-screen py-16 px-4 bg-gradient-to-b from-slate-50 via-white to-slate-50">
	<div class="max-w-4xl mx-auto">
		<!-- Back Link -->
		<a
			href="/"
			class="inline-flex items-center gap-2 text-[#0369A1] hover:text-[#0284C7] transition-colors mb-8 group"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-5 w-5 transform group-hover:-translate-x-1 transition-transform"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2.5"
					d="M10 19l-7-7m0 0l7-7m-7 7h18"
				/>
			</svg>
			<span class="font-bold">Back to Home</span>
		</a>

		<!-- Hero Section -->
		<div
			class="relative overflow-hidden bg-gradient-to-br from-[#0B3C5D] via-[#0D5C75] to-[#0284C7] rounded-3xl p-8 sm:p-12 mb-12 text-white shadow-xl border border-sky-800"
		>
			<!-- Decorative glowing orb -->
			<div class="absolute -right-16 -top-16 w-64 h-64 bg-sky-400/20 rounded-full blur-3xl"></div>
			<div
				class="absolute -left-20 -bottom-20 w-80 h-80 bg-[#059669]/10 rounded-full blur-3xl"
			></div>

			<div class="relative flex flex-col md:flex-row items-center gap-8 z-10">
				<div class="flex-1">
					<span
						class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sky-500/20 text-sky-200 border border-sky-400/30 mb-4 tracking-wide uppercase"
					>
						Next-Gen AI Agency
					</span>
					<h1 class="text-3xl sm:text-5xl font-black tracking-tight mb-4 leading-tight">
						Why Job-Vite Beats <br class="hidden sm:inline" />Single-Prompt AI
					</h1>
					<p class="text-base sm:text-lg text-slate-100/90 leading-relaxed max-w-2xl">
						Standard AI platforms throw your resume and a job description into a single, generic
						prompt. The result? A letter littered with generic corporate fluff, obvious AI tells,
						and factual hallucinations.
					</p>
					<p
						class="text-base sm:text-lg text-slate-100/90 leading-relaxed max-w-2xl mt-3 font-semibold text-sky-200"
					>
						Job-Vite solves this by assembling a <strong
							>Sequential Crew of 3 Specialized AI Agents</strong
						> to research, draft, and polish your application just like a elite human editorial agency.
					</p>
				</div>
			</div>
		</div>

		<!-- Flowchart / Pipeline -->
		<div class="bg-white rounded-2xl border border-[#E2E8F0] shadow-sm p-6 sm:p-8 mb-12">
			<h2 class="text-xl sm:text-2xl font-extrabold text-[#0F172A] mb-8 text-center">
				The Editorial Pipeline Logic
			</h2>

			<div class="flex flex-col md:flex-row items-center justify-between gap-4 md:gap-2 relative">
				<!-- Step 1: Input -->
				<div
					class="flex flex-col items-center text-center p-4 bg-slate-50 border border-slate-100 rounded-xl w-full md:w-1/4"
				>
					<div
						class="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-600 shadow-sm mb-2 text-sm"
					>
						INPUT
					</div>
					<h4 class="font-bold text-slate-800 text-xs uppercase tracking-wider mb-1">
						Your Context
					</h4>
					<p class="text-[11px] text-slate-500">CV & Job Description</p>
				</div>

				<!-- Connector -->
				<div class="text-[#0369A1] rotate-90 md:rotate-0">
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
							stroke-width="2.5"
							d="M13 5l7 7-7 7M5 5l7 7-7 7"
						/>
					</svg>
				</div>

				<!-- Step 2: Analyst -->
				<div
					class="flex flex-col items-center text-center p-4 bg-blue-50/50 border border-blue-100/50 rounded-xl w-full md:w-1/4"
				>
					<div
						class="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold shadow-sm mb-2 text-sm"
					>
						1
					</div>
					<h4 class="font-bold text-blue-800 text-xs uppercase tracking-wider mb-1">
						Profile Analyst
					</h4>
					<p class="text-[11px] text-blue-500">Extracts Hard Facts</p>
				</div>

				<!-- Connector -->
				<div class="text-[#0369A1] rotate-90 md:rotate-0">
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
							stroke-width="2.5"
							d="M13 5l7 7-7 7M5 5l7 7-7 7"
						/>
					</svg>
				</div>

				<!-- Step 3: Copywriter -->
				<div
					class="flex flex-col items-center text-center p-4 bg-emerald-50/50 border border-emerald-100/50 rounded-xl w-full md:w-1/4"
				>
					<div
						class="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold shadow-sm mb-2 text-sm"
					>
						2
					</div>
					<h4 class="font-bold text-emerald-800 text-xs uppercase tracking-wider mb-1">
						Copywriter
					</h4>
					<p class="text-[11px] text-emerald-500">Builds Narrative</p>
				</div>

				<!-- Connector -->
				<div class="text-[#0369A1] rotate-90 md:rotate-0">
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
							stroke-width="2.5"
							d="M13 5l7 7-7 7M5 5l7 7-7 7"
						/>
					</svg>
				</div>

				<!-- Step 4: Editor -->
				<div
					class="flex flex-col items-center text-center p-4 bg-amber-50/50 border border-amber-100/50 rounded-xl w-full md:w-1/4"
				>
					<div
						class="w-10 h-10 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center font-bold shadow-sm mb-2 text-sm"
					>
						3
					</div>
					<h4 class="font-bold text-amber-800 text-xs uppercase tracking-wider mb-1">
						Strict Editor
					</h4>
					<p class="text-[11px] text-amber-500">Polishes & Enforces Limits</p>
				</div>
			</div>
		</div>

		<!-- The 3 Experts Bento Grid -->
		<h2 class="text-2xl sm:text-3xl font-extrabold text-[#0F172A] mb-8 text-center">
			Meet Your Personal 3-Expert AI Crew
		</h2>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
			<!-- Expert 1: Analyst -->
			<div
				class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between hover:shadow-md transition-all duration-300 hover:-translate-y-1"
			>
				<div>
					<div class="flex items-center justify-between mb-4">
						<span
							class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-100 text-blue-700 border border-blue-200"
						>
							Precision Analyst
						</span>
						<span class="text-xs font-semibold text-slate-400">Temp: 0.1</span>
					</div>
					<div
						class="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600 mb-4 shadow-inner"
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
								d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
							/>
						</svg>
					</div>
					<h3 class="text-xl font-bold text-slate-800 mb-2">1. The Profile Analyst</h3>
					<p class="text-sm text-slate-600 leading-relaxed mb-4">
						A ruthless data-miner. Running at an analytical temperature of <code>0.1</code>, this
						agent cross-references the candidate's history with the Job Description to isolate the
						<strong>top 3 strongest overlaps</strong>.
					</p>
				</div>
				<div class="bg-slate-50 rounded-xl p-3 border border-slate-100">
					<h5 class="text-[11px] font-bold text-slate-500 uppercase tracking-wide mb-1">
						Crucial Task:
					</h5>
					<p class="text-xs text-slate-600 italic">
						"Extract raw facts. Avoid any letters. Create a cold strategy brief and flag missing
						skills to downplay."
					</p>
				</div>
			</div>

			<!-- Expert 2: Copywriter -->
			<div
				class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between hover:shadow-md transition-all duration-300 hover:-translate-y-1"
			>
				<div>
					<div class="flex items-center justify-between mb-4">
						<span
							class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-700 border border-emerald-200"
						>
							Persuasive Storyteller
						</span>
						<span class="text-xs font-semibold text-slate-400">Temp: 0.7</span>
					</div>
					<div
						class="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center text-emerald-600 mb-4 shadow-inner"
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
								d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
							/>
						</svg>
					</div>
					<h3 class="text-xl font-bold text-slate-800 mb-2">2. Expert Copywriter</h3>
					<p class="text-sm text-slate-600 leading-relaxed mb-4">
						A master persuasive writer. Operating at a creative temperature of <code>0.7</code>,
						this agent takes the Analyst's facts and synthesizes them into an engaging, cohesive
						career narrative.
					</p>
				</div>
				<div class="bg-slate-50 rounded-xl p-3 border border-slate-100">
					<h5 class="text-[11px] font-bold text-slate-500 uppercase tracking-wide mb-1">
						Crucial Task:
					</h5>
					<p class="text-xs text-slate-600 italic">
						"Translate dry analytical briefs into human-grade story copy that binds past results to
						the target company's future needs."
					</p>
				</div>
			</div>

			<!-- Expert 3: Editor -->
			<div
				class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between hover:shadow-md transition-all duration-300 hover:-translate-y-1"
			>
				<div>
					<div class="flex items-center justify-between mb-4">
						<span
							class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-700 border border-amber-200"
						>
							Strict Quality Control
						</span>
						<span class="text-xs font-semibold text-slate-400">Temp: 0.3</span>
					</div>
					<div
						class="w-12 h-12 bg-amber-50 rounded-xl flex items-center justify-center text-amber-600 mb-4 shadow-inner"
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
								d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
					</div>
					<h3 class="text-xl font-bold text-slate-800 mb-2">3. The Strict Editor</h3>
					<p class="text-sm text-slate-600 leading-relaxed mb-4">
						The ultimate gatekeeper. Operating at a strict temperature of <code>0.3</code>, this
						agent edits the copywriter's draft to remove buzzwords, corporate fluff, and typical AI
						tells.
					</p>
				</div>
				<div class="bg-slate-50 rounded-xl p-3 border border-slate-100">
					<h5 class="text-[11px] font-bold text-slate-500 uppercase tracking-wide mb-1">
						Crucial Task:
					</h5>
					<p class="text-xs text-slate-600 italic">
						"Delete sycophantic language and AI indicators ('delve', 'testament to'). Enforce a
						strict sub-300-word limit."
					</p>
				</div>
			</div>
		</div>

		<!-- Why This Beats The Bots Section -->
		<div class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-8 mb-8">
			<div class="flex items-center gap-3 mb-6">
				<div class="p-2 bg-[#EFF6FF] rounded-lg text-[#0369A1]">
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
				</div>
				<h2 class="text-2xl font-bold text-[#0F172A]">Why Separating Tasks Works</h2>
			</div>

			<div class="space-y-4 text-[#334155] leading-relaxed">
				<p>
					In software and cognitive architectures, trying to make an LLM perform complex reasoning,
					drafting, and editing in a single prompt is highly error-prone. The model gets overwhelmed
					trying to balance factual alignment with creative writing and formatting constraints,
					leading to **hallucinations**.
				</p>
				<p>
					By dividing the cover letter generation into a **sequential workflow**, we isolate
					responsibilities:
				</p>
				<ul class="list-disc pl-6 space-y-2">
					<li>
						<strong>Zero Hallucinations</strong>: The Analyst acts as the factual source of truth.
						The Copywriter can only write using the specific points validated by the Analyst.
					</li>
					<li>
						<strong>No Obvious AI Tells</strong>: Typical LLM output contains clichés like
						<em>"delve into," "in today's fast-paced world,"</em>
						or <em>"testament to."</em> The Editor strictly filters out these patterns, making the cover
						letter indistinguishable from human copywriting.
					</li>
					<li>
						<strong>ATS Keyword Alignment</strong>: Because the Analyst extracts terms directly from
						the job posting, the copywriter naturally integrates keywords to boost your ATS match
						score without "keyword-stuffing."
					</li>
				</ul>
			</div>
		</div>

		<!-- Call to Action -->
		<div
			class="bg-gradient-to-r from-[#F8FAFC] to-[#EFF6FF] rounded-2xl border-2 border-[#0369A1]/20 p-8 sm:p-12 text-center"
		>
			<h3 class="text-2xl sm:text-3xl font-extrabold text-[#0F172A] mb-3">
				Ready to Deploy Your Expert Crew?
			</h3>
			<p class="text-[#334155] mb-6 max-w-2xl mx-auto text-sm sm:text-base">
				Stop submitting letters that sound like robotic templates. Let our 3-Expert Sequential Crew
				draft a unique, ATS-optimized cover letter for you in seconds.
			</p>
			<a
				href="/"
				class="inline-block bg-[#0369A1] text-white font-bold px-8 py-3.5 rounded-xl hover:bg-[#0284C7] transition-all shadow-md hover:shadow-lg transform hover:scale-105"
			>
				Generate Your Cover Letter
			</a>
		</div>
	</div>
</div>
