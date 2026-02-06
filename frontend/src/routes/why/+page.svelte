<script lang="ts">
    // SvelteKit may pass `data` and `params` to pages — declare to prevent runtime warnings
    export let data: any = {};
    export let params: Record<string, string> = {};
</script>

<svelte:head>
    <title>Why Use Vite a Job? - Beat the ATS</title>
</svelte:head>

<div class="min-h-screen py-16 px-4 bg-gradient-to-b from-white to-slate-50">
    <div class="max-w-4xl mx-auto">
        <!-- Back Link -->
        <a
            href="/"
            class="inline-flex items-center gap-2 text-[#0369A1] hover:text-[#0284C7] transition-colors mb-8"
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
            <span class="font-semibold">Back to Home</span>
        </a>

        <!-- Hero Section -->
        <div
            class="bg-gradient-to-br from-[#0369A1] to-[#0284C7] rounded-2xl p-12 mb-12 text-white shadow-xl"
        >
            <div class="flex items-start gap-4 mb-6">
                <div class="p-3 bg-white/20 rounded-lg backdrop-blur-sm">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-8 w-8"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                </div>
                <div>
                    <h1 class="text-4xl font-extrabold mb-4">
                        Why Use Vite a Job?
                    </h1>
                    <p class="text-xl text-white/90 leading-relaxed">
                        <strong>75% of resumes are rejected by ATS bots</strong>
                        before a human ever sees them. Vite a Job uses AI to ensure
                        your cover letter speaks the exact language of the job description,
                        helping you pass the automated filters.
                    </p>
                </div>
            </div>
        </div>

        <!-- What is ATS Section -->
        <div
            class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-8 mb-8"
        >
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
                <h2 class="text-2xl font-bold text-[#0F172A]">What is ATS?</h2>
            </div>

            <div class="space-y-4 text-[#334155] leading-relaxed">
                <p>
                    <strong>ATS (Applicant Tracking System)</strong> is software
                    used by employers to automatically filter job applications. It's
                    the gatekeeper between you and the hiring manager.
                </p>
                <p>
                    When you submit your resume and cover letter online, they
                    don't go straight to a human. First, the ATS:
                </p>
                <ul class="list-disc pl-6 space-y-2">
                    <li>
                        <strong>Parses your documents</strong> - Extracts text from
                        your PDF/Word files
                    </li>
                    <li>
                        <strong>Scans for keywords</strong> - Looks for specific
                        terms from the job description
                    </li>
                    <li>
                        <strong>Ranks candidates</strong> - Gives your application
                        a match score
                    </li>
                </ul>
                <p>
                    Recruiters often only review the <strong
                        >top 10-20% of matches</strong
                    >. If your application doesn't speak the ATS language, it
                    might never reach a human.
                </p>
            </div>
        </div>

        <!-- How Vite a Job Helps Section -->
        <div
            class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-8 mb-8"
        >
            <div class="flex items-center gap-3 mb-6">
                <div class="p-2 bg-[#ECFDF5] rounded-lg text-[#059669]">
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
                <h2 class="text-2xl font-bold text-[#0F172A]">
                    How Vite a Job Optimizes for ATS
                </h2>
            </div>

            <div class="space-y-6">
                <div class="flex gap-4">
                    <div
                        class="flex-shrink-0 w-8 h-8 bg-[#0369A1] text-white rounded-full flex items-center justify-center font-bold text-sm"
                    >
                        1
                    </div>
                    <div>
                        <h3 class="font-semibold text-[#0F172A] mb-2">
                            Keyword Analysis
                        </h3>
                        <p class="text-[#334155]">
                            Our AI analyzes the job description to identify the
                            exact keywords, skills, and terminology employers
                            are looking for.
                        </p>
                    </div>
                </div>

                <div class="flex gap-4">
                    <div
                        class="flex-shrink-0 w-8 h-8 bg-[#0369A1] text-white rounded-full flex items-center justify-center font-bold text-sm"
                    >
                        2
                    </div>
                    <div>
                        <h3 class="font-semibold text-[#0F172A] mb-2">
                            Smart Integration
                        </h3>
                        <p class="text-[#334155]">
                            Generates cover letters that naturally incorporate
                            these keywords while maintaining a professional,
                            personalized tone.
                        </p>
                    </div>
                </div>

                <div class="flex gap-4">
                    <div
                        class="flex-shrink-0 w-8 h-8 bg-[#0369A1] text-white rounded-full flex items-center justify-center font-bold text-sm"
                    >
                        3
                    </div>
                    <div>
                        <h3 class="font-semibold text-[#0F172A] mb-2">
                            Higher Match Score
                        </h3>
                        <p class="text-[#334155]">
                            By using the exact language from the job posting,
                            your cover letter scores higher in ATS ranking,
                            increasing your chances of reaching the recruiter.
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Call to Action -->
        <div
            class="bg-gradient-to-r from-[#F8FAFC] to-[#EFF6FF] rounded-xl border-2 border-[#0369A1]/20 p-8 text-center"
        >
            <h3 class="text-2xl font-bold text-[#0F172A] mb-3">
                Ready to Beat the Bots?
            </h3>
            <p class="text-[#334155] mb-6 max-w-2xl mx-auto">
                Stop wasting time on applications that never reach human eyes.
                Generate ATS-optimized cover letters in seconds.
            </p>
            <a
                href="/"
                class="inline-block bg-[#0369A1] text-white font-semibold px-8 py-3 rounded-lg hover:bg-[#0284C7] transition-colors shadow-lg hover:shadow-xl transform hover:scale-105 transition-transform"
            >
                Generate Your Cover Letter
            </a>
        </div>
    </div>
</div>
