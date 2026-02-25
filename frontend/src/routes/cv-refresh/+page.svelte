<script lang="ts">
    import SEO from "$lib/components/SEO.svelte";
    import {
        uploadCV,
        getCVTemplates,
        generateCV,
        type CVData,
        type CVContact,
        type CVExperience,
        type CVEducation,
        type CVTemplate,
    } from "$lib/api";

    // ── State ──────────────────────────────────────────────────────────
    let step: "upload" | "review" | "generate" = "upload";
    let loading = false;
    let error = "";

    // Upload
    let dragover = false;

    // Parsed CV data
    let cvData: CVData = {
        contact: { name: "", email: "", phone: "", linkedin: "", address: "" },
        summary: "",
        experiences: [],
        education: [],
        skills: [],
        languages: [],
    };

    // Templates
    let templates: CVTemplate[] = [];
    let selectedTemplate = "modern_single";
    let modernLayout: "single" | "two" = "single";

    // Skills / Languages inline editing
    let newSkill = "";
    let newLanguage = "";

    // ── Upload handlers ────────────────────────────────────────────────
    function handleDragover(e: DragEvent) {
        e.preventDefault();
        dragover = true;
    }
    function handleDragleave() {
        dragover = false;
    }
    async function handleDrop(e: DragEvent) {
        e.preventDefault();
        dragover = false;
        const file = e.dataTransfer?.files[0];
        if (file) await processFile(file);
    }
    async function handleFileInput(e: Event) {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        if (file) await processFile(file);
    }

    async function processFile(file: File) {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            error = "Please upload a PDF file.";
            return;
        }
        error = "";
        loading = true;
        try {
            cvData = await uploadCV(file);
            step = "review";
        } catch (e: any) {
            error = e.message || "Failed to parse CV";
        } finally {
            loading = false;
        }
    }

    // ── Experience / Education helpers ──────────────────────────────────
    function addExperience() {
        cvData.experiences = [
            ...cvData.experiences,
            {
                title: "",
                company: "",
                start_date: "",
                end_date: "",
                description: "",
            },
        ];
    }
    function removeExperience(i: number) {
        cvData.experiences = cvData.experiences.filter((_, idx) => idx !== i);
    }
    function addEducation() {
        cvData.education = [
            ...cvData.education,
            { degree: "", institution: "", start_date: "", end_date: "" },
        ];
    }
    function removeEducation(i: number) {
        cvData.education = cvData.education.filter((_, idx) => idx !== i);
    }

    // ── Skills / Languages helpers ─────────────────────────────────────
    function addSkill() {
        if (newSkill.trim()) {
            cvData.skills = [...cvData.skills, newSkill.trim()];
            newSkill = "";
        }
    }
    function removeSkill(i: number) {
        cvData.skills = cvData.skills.filter((_, idx) => idx !== i);
    }
    function addLanguage() {
        if (newLanguage.trim()) {
            cvData.languages = [...cvData.languages, newLanguage.trim()];
            newLanguage = "";
        }
    }
    function removeLanguage(i: number) {
        cvData.languages = cvData.languages.filter((_, idx) => idx !== i);
    }

    // ── Template selection & generation ────────────────────────────────
    async function goToGenerate() {
        loading = true;
        error = "";
        try {
            templates = await getCVTemplates();
        } catch (e: any) {
            error = e.message || "Failed to load templates";
        } finally {
            loading = false;
        }
        step = "generate";
    }

    async function handleGenerate() {
        loading = true;
        error = "";
        try {
            // Respect the layout toggle if modern is selected
            let actualTemplate = selectedTemplate;
            if (selectedTemplate.startsWith("modern")) {
                actualTemplate =
                    modernLayout === "single" ? "modern_single" : "modern";
            }

            const blob = await generateCV(cvData, actualTemplate);
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `cv_${cvData.contact.name.replace(/\s+/g, "_") || "refreshed"}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        } catch (e: any) {
            error = e.message || "Failed to generate CV";
        } finally {
            loading = false;
        }
    }

    function goBack() {
        if (step === "generate") step = "review";
        else if (step === "review") step = "upload";
    }

    function isStepAvailable(s: string) {
        if (s === "upload") return true;
        if (s === "review")
            return cvData.contact.name !== "" || cvData.experiences.length > 0;
        if (s === "generate")
            return (
                (cvData.contact.name !== "" || cvData.experiences.length > 0) &&
                step !== "upload"
            );
        return false;
    }

    function handleStepClick(s: string) {
        if (!isStepAvailable(s)) return;
        if (s === "generate") {
            goToGenerate();
        } else {
            step = s as "upload" | "review" | "generate";
        }
    }
</script>

<SEO
    title="CV Refresh — Modernize Your Resume | Vite a Job"
    description="Upload your old CV to get a clean, modern PDF. AI parses your experience — you review & customize — then download a professional template."
    canonical="https://viteajob.com/cv-refresh"
/>

<div class="min-h-screen py-16 px-4 bg-gradient-to-b from-white to-slate-50">
    <div class="max-w-4xl mx-auto">
        <!-- Back -->
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

        <!-- Hero -->
        <div
            class="bg-gradient-to-br from-[#0369A1] to-[#0284C7] rounded-2xl p-10 mb-10 text-white shadow-xl"
        >
            <div class="flex items-start gap-4">
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
                            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                    </svg>
                </div>
                <div>
                    <h1 class="text-3xl font-extrabold mb-2">CV Refresh</h1>
                    <p class="text-lg text-white/90 leading-relaxed">
                        Upload your old CV, review the parsed data, and download
                        a fresh, modern PDF.
                    </p>
                </div>
            </div>
        </div>

        <!-- Step Indicator -->
        <div class="flex items-center justify-center gap-2 mb-10">
            {#each [{ key: "upload", label: "Upload" }, { key: "review", label: "Review & Edit" }, { key: "generate", label: "Template & Download" }] as s, i}
                <div class="flex items-center gap-2">
                    <button
                        on:click={() => handleStepClick(s.key)}
                        class="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300
                            {step === s.key
                            ? 'bg-[#0369A1] text-white shadow-lg scale-110'
                            : (s.key === 'upload' &&
                                    (step === 'review' ||
                                        step === 'generate')) ||
                                (s.key === 'review' && step === 'generate')
                              ? 'bg-emerald-500 text-white'
                              : 'bg-slate-200 text-slate-500'} 
                            {isStepAvailable(s.key)
                            ? 'cursor-pointer hover:opacity-80'
                            : 'cursor-default'}"
                    >
                        {#if (s.key === "upload" && (step === "review" || step === "generate")) || (s.key === "review" && step === "generate")}
                            ✓
                        {:else}
                            {i + 1}
                        {/if}
                    </button>
                    <span
                        class="text-sm font-medium text-slate-600 hidden sm:inline"
                        >{s.label}</span
                    >
                    {#if i < 2}
                        <div class="w-12 h-[2px] bg-slate-200 mx-1"></div>
                    {/if}
                </div>
            {/each}
        </div>

        <!-- Error -->
        {#if error}
            <div
                class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center gap-3"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-5 w-5 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                    />
                </svg>
                <span>{error}</span>
            </div>
        {/if}

        <!-- ═══════════════════════════════════════════════════════════ -->
        <!-- STEP 1: Upload                                             -->
        <!-- ═══════════════════════════════════════════════════════════ -->
        {#if step === "upload"}
            <div
                class="bg-white rounded-2xl border-2 border-dashed transition-all duration-300 p-16 text-center cursor-pointer
                    {dragover
                    ? 'border-[#0369A1] bg-blue-50/50 scale-[1.01]'
                    : 'border-slate-300 hover:border-[#0369A1]'}"
                on:dragover={handleDragover}
                on:dragleave={handleDragleave}
                on:drop={handleDrop}
                role="button"
                tabindex="0"
            >
                {#if loading}
                    <div class="flex flex-col items-center gap-4">
                        <div
                            class="w-16 h-16 border-4 border-[#0369A1] border-t-transparent rounded-full animate-spin"
                        ></div>
                        <p class="text-lg font-semibold text-[#0F172A]">
                            Parsing your CV…
                        </p>
                        <p class="text-sm text-slate-500">
                            This may take a few seconds
                        </p>
                    </div>
                {:else}
                    <div class="flex flex-col items-center gap-4">
                        <div class="p-4 bg-[#EFF6FF] rounded-full">
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                class="h-12 w-12 text-[#0369A1]"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                                />
                            </svg>
                        </div>
                        <div>
                            <p class="text-xl font-bold text-[#0F172A] mb-1">
                                Drop your CV here
                            </p>
                            <p class="text-slate-500">
                                or click to browse • PDF only
                            </p>
                        </div>
                        <label
                            class="mt-2 inline-block bg-[#0369A1] text-white font-semibold px-6 py-2.5 rounded-lg hover:bg-[#0284C7] transition-colors cursor-pointer shadow-md"
                        >
                            Choose File
                            <input
                                type="file"
                                accept=".pdf"
                                class="hidden"
                                on:change={handleFileInput}
                            />
                        </label>
                    </div>
                {/if}
            </div>

            <!-- ═══════════════════════════════════════════════════════════ -->
            <!-- STEP 2: Review & Edit                                      -->
            <!-- ═══════════════════════════════════════════════════════════ -->
        {:else if step === "review"}
            <div class="space-y-6">
                <!-- Contact Information -->
                <div
                    class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6"
                >
                    <h2
                        class="text-xl font-bold text-[#0F172A] mb-4 flex items-center gap-2"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            class="h-5 w-5 text-[#0369A1]"
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
                        Contact Information
                    </h2>
                    <div class="grid md:grid-cols-2 gap-4">
                        <div>
                            <label
                                for="full-name"
                                class="block text-sm font-medium text-slate-600 mb-1"
                                >Full Name</label
                            >
                            <input
                                type="text"
                                id="full-name"
                                bind:value={cvData.contact.name}
                                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none transition-all"
                            />
                        </div>
                        <div>
                            <label
                                for="email"
                                class="block text-sm font-medium text-slate-600 mb-1"
                                >Email</label
                            >
                            <input
                                type="email"
                                id="email"
                                bind:value={cvData.contact.email}
                                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none transition-all"
                            />
                        </div>
                        <div>
                            <label
                                for="phone"
                                class="block text-sm font-medium text-slate-600 mb-1"
                                >Phone</label
                            >
                            <input
                                type="tel"
                                id="phone"
                                bind:value={cvData.contact.phone}
                                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none transition-all"
                            />
                        </div>
                        <div>
                            <label
                                for="linkedin"
                                class="block text-sm font-medium text-slate-600 mb-1"
                                >LinkedIn</label
                            >
                            <input
                                type="url"
                                id="linkedin"
                                bind:value={cvData.contact.linkedin}
                                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none transition-all"
                            />
                        </div>
                        <div class="md:col-span-2">
                            <label
                                for="address"
                                class="block text-sm font-medium text-slate-600 mb-1"
                                >Address</label
                            >
                            <input
                                type="text"
                                id="address"
                                bind:value={cvData.contact.address}
                                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none transition-all"
                            />
                        </div>
                    </div>
                </div>

                <!-- Summary -->
                <div
                    class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6"
                >
                    <h2 class="text-xl font-bold text-[#0F172A] mb-4">
                        Professional Summary
                    </h2>
                    <textarea
                        bind:value={cvData.summary}
                        rows="4"
                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none transition-all resize-y"
                        placeholder="Brief professional summary…"
                    ></textarea>
                </div>

                <!-- Experience -->
                <div
                    class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6"
                >
                    <div class="flex items-center justify-between mb-4">
                        <h2
                            class="text-xl font-bold text-[#0F172A] flex items-center gap-2"
                        >
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                class="h-5 w-5 text-[#0369A1]"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                                />
                            </svg>
                            Experience
                        </h2>
                        <button
                            on:click={addExperience}
                            class="text-sm bg-[#EFF6FF] text-[#0369A1] px-3 py-1.5 rounded-lg hover:bg-[#DBEAFE] transition-colors font-medium"
                        >
                            + Add
                        </button>
                    </div>
                    {#each cvData.experiences as exp, i}
                        <div
                            class="border border-slate-200 rounded-lg p-4 mb-4 relative group"
                        >
                            <button
                                on:click={() => removeExperience(i)}
                                class="absolute top-2 right-2 p-1 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                                title="Remove"
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
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                            <div class="grid md:grid-cols-2 gap-3 mb-3">
                                <div>
                                    <label
                                        for="exp-title-{i}"
                                        class="block text-xs font-medium text-slate-500 mb-1"
                                        >Job Title</label
                                    >
                                    <input
                                        type="text"
                                        id="exp-title-{i}"
                                        bind:value={exp.title}
                                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm"
                                    />
                                </div>
                                <div>
                                    <label
                                        for="exp-company-{i}"
                                        class="block text-xs font-medium text-slate-500 mb-1"
                                        >Company</label
                                    >
                                    <input
                                        type="text"
                                        id="exp-company-{i}"
                                        bind:value={exp.company}
                                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm"
                                    />
                                </div>
                                <div>
                                    <label
                                        for="exp-start-{i}"
                                        class="block text-xs font-medium text-slate-500 mb-1"
                                        >Start Date</label
                                    >
                                    <input
                                        type="text"
                                        id="exp-start-{i}"
                                        bind:value={exp.start_date}
                                        placeholder="e.g. Jan 2020"
                                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm"
                                    />
                                </div>
                                <div>
                                    <label
                                        for="exp-end-{i}"
                                        class="block text-xs font-medium text-slate-500 mb-1"
                                        >End Date</label
                                    >
                                    <input
                                        type="text"
                                        id="exp-end-{i}"
                                        bind:value={exp.end_date}
                                        placeholder="e.g. Present"
                                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm"
                                    />
                                </div>
                            </div>
                            <div>
                                <label
                                    for="exp-desc-{i}"
                                    class="block text-xs font-medium text-slate-500 mb-1"
                                    >Description</label
                                >
                                <textarea
                                    id="exp-desc-{i}"
                                    bind:value={exp.description}
                                    rows="2"
                                    class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm resize-y"
                                ></textarea>
                            </div>
                        </div>
                    {/each}
                    {#if cvData.experiences.length === 0}
                        <p class="text-slate-400 text-sm italic">
                            No experiences — click "+ Add" above.
                        </p>
                    {/if}
                </div>

                <!-- Education -->
                <div
                    class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6"
                >
                    <div class="flex items-center justify-between mb-4">
                        <h2
                            class="text-xl font-bold text-[#0F172A] flex items-center gap-2"
                        >
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                class="h-5 w-5 text-[#0369A1]"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path d="M12 14l9-5-9-5-9 5 9 5z" />
                                <path
                                    d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"
                                />
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222"
                                />
                            </svg>
                            Education
                        </h2>
                        <button
                            on:click={addEducation}
                            class="text-sm bg-[#EFF6FF] text-[#0369A1] px-3 py-1.5 rounded-lg hover:bg-[#DBEAFE] transition-colors font-medium"
                        >
                            + Add
                        </button>
                    </div>
                    {#each cvData.education as edu, i}
                        <div
                            class="border border-slate-200 rounded-lg p-4 mb-4 relative group"
                        >
                            <button
                                on:click={() => removeEducation(i)}
                                class="absolute top-2 right-2 p-1 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                                title="Remove"
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
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                            </button>
                            <div class="grid md:grid-cols-2 gap-3">
                                <div>
                                    <label
                                        for="edu-degree-{i}"
                                        class="block text-xs font-medium text-slate-500 mb-1"
                                        >Degree</label
                                    >
                                    <input
                                        type="text"
                                        id="edu-degree-{i}"
                                        bind:value={edu.degree}
                                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm"
                                    />
                                </div>
                                <div>
                                    <label
                                        for="edu-institution-{i}"
                                        class="block text-xs font-medium text-slate-500 mb-1"
                                        >Institution</label
                                    >
                                    <input
                                        type="text"
                                        id="edu-institution-{i}"
                                        bind:value={edu.institution}
                                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm"
                                    />
                                </div>
                                <div>
                                    <label
                                        for="edu-start-{i}"
                                        class="block text-xs font-medium text-slate-500 mb-1"
                                        >Start Date</label
                                    >
                                    <input
                                        type="text"
                                        id="edu-start-{i}"
                                        bind:value={edu.start_date}
                                        placeholder="e.g. 2016"
                                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm"
                                    />
                                </div>
                                <div>
                                    <label
                                        for="edu-end-{i}"
                                        class="block text-xs font-medium text-slate-500 mb-1"
                                        >End Date</label
                                    >
                                    <input
                                        type="text"
                                        id="edu-end-{i}"
                                        bind:value={edu.end_date}
                                        placeholder="e.g. 2020"
                                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm"
                                    />
                                </div>
                            </div>
                        </div>
                    {/each}
                    {#if cvData.education.length === 0}
                        <p class="text-slate-400 text-sm italic">
                            No education entries — click "+ Add" above.
                        </p>
                    {/if}
                </div>

                <!-- Skills -->
                <div
                    class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6"
                >
                    <h2 class="text-xl font-bold text-[#0F172A] mb-4">
                        Skills
                    </h2>
                    <div class="flex flex-wrap gap-2 mb-3">
                        {#each cvData.skills as skill, i}
                            <span
                                class="inline-flex items-center gap-1 bg-[#EFF6FF] text-[#0369A1] px-3 py-1 rounded-full text-sm font-medium"
                            >
                                {skill}
                                <button
                                    on:click={() => removeSkill(i)}
                                    class="hover:text-red-500 transition-colors"
                                    >×</button
                                >
                            </span>
                        {/each}
                    </div>
                    <div class="flex gap-2">
                        <input
                            type="text"
                            bind:value={newSkill}
                            placeholder="Add a skill…"
                            class="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm"
                            on:keydown={(e) => e.key === "Enter" && addSkill()}
                        />
                        <button
                            on:click={addSkill}
                            class="px-4 py-2 bg-[#0369A1] text-white rounded-lg hover:bg-[#0284C7] transition-colors text-sm font-medium"
                        >
                            Add
                        </button>
                    </div>
                </div>

                <!-- Languages -->
                <div
                    class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6"
                >
                    <h2 class="text-xl font-bold text-[#0F172A] mb-4">
                        Languages
                    </h2>
                    <div class="flex flex-wrap gap-2 mb-3">
                        {#each cvData.languages as lang, i}
                            <span
                                class="inline-flex items-center gap-1 bg-[#ECFDF5] text-[#059669] px-3 py-1 rounded-full text-sm font-medium"
                            >
                                {lang}
                                <button
                                    on:click={() => removeLanguage(i)}
                                    class="hover:text-red-500 transition-colors"
                                    >×</button
                                >
                            </span>
                        {/each}
                    </div>
                    <div class="flex gap-2">
                        <input
                            type="text"
                            bind:value={newLanguage}
                            placeholder="Add a language…"
                            class="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0369A1] focus:border-transparent outline-none text-sm"
                            on:keydown={(e) =>
                                e.key === "Enter" && addLanguage()}
                        />
                        <button
                            on:click={addLanguage}
                            class="px-4 py-2 bg-[#059669] text-white rounded-lg hover:bg-[#047857] transition-colors text-sm font-medium"
                        >
                            Add
                        </button>
                    </div>
                </div>

                <!-- Navigation -->
                <div class="flex justify-between pt-2">
                    <button
                        on:click={goBack}
                        class="px-5 py-2.5 border border-slate-300 text-slate-600 rounded-lg hover:bg-slate-50 transition-colors font-medium"
                    >
                        ← Back
                    </button>
                    <button
                        on:click={goToGenerate}
                        class="px-6 py-2.5 bg-[#0369A1] text-white rounded-lg hover:bg-[#0284C7] transition-colors font-semibold shadow-md hover:shadow-lg"
                    >
                        Choose Template →
                    </button>
                </div>
            </div>

            <!-- ═══════════════════════════════════════════════════════════ -->
            <!-- STEP 3: Template & Generate                                -->
            <!-- ═══════════════════════════════════════════════════════════ -->
        {:else if step === "generate"}
            <div class="space-y-6">
                <div
                    class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6"
                >
                    <h2 class="text-xl font-bold text-[#0F172A] mb-6">
                        Choose a Template
                    </h2>
                    <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {#each templates.filter((t) => t.name !== "modern_single") as t}
                            <button
                                on:click={() => (selectedTemplate = t.name)}
                                class="border-2 rounded-xl p-5 text-left transition-all duration-200 hover:shadow-md
                                    {selectedTemplate.startsWith(t.name)
                                    ? 'border-[#0369A1] bg-[#EFF6FF] shadow-md'
                                    : 'border-slate-200 hover:border-slate-300'}"
                            >
                                <div class="flex items-center gap-3 mb-2">
                                    <div
                                        class="w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold
                                            {selectedTemplate.startsWith(t.name)
                                            ? 'bg-[#0369A1] text-white'
                                            : 'bg-slate-100 text-slate-500'}"
                                    >
                                        {t.label[0]}
                                    </div>
                                    <div>
                                        <h3
                                            class="font-semibold text-[#0F172A]"
                                        >
                                            {t.label}
                                        </h3>
                                    </div>
                                </div>
                                <p class="text-sm text-slate-500">
                                    {t.description}
                                </p>
                                {#if selectedTemplate.startsWith(t.name)}
                                    <div
                                        class="mt-2 text-xs font-semibold text-[#0369A1]"
                                    >
                                        ✓ Selected
                                    </div>
                                {/if}
                            </button>
                        {/each}
                        {#if templates.length === 0 && !loading}
                            <p class="text-slate-400 italic col-span-full">
                                No templates found.
                            </p>
                        {/if}
                    </div>

                    <!-- Layout Selector if Modern is chosen -->
                    {#if selectedTemplate.startsWith("modern")}
                        <div
                            class="mt-6 p-5 border-2 border-[#0369A1] bg-[#EFF6FF] rounded-xl animate-fade-in"
                        >
                            <h3 class="font-bold text-lg mb-3">Layout Style</h3>
                            <div class="flex flex-col sm:flex-row gap-4">
                                <!-- Single Column (Default) -->
                                <button
                                    on:click={() => (modernLayout = "single")}
                                    class="flex-1 border-2 rounded-lg p-4 text-left transition-all
                                        {modernLayout === 'single'
                                        ? 'border-[#0369A1] bg-white shadow-sm ring-1 ring-[#0369A1]'
                                        : 'border-slate-300 bg-white/50 opacity-70 hover:opacity-100 hover:border-slate-400'}"
                                >
                                    <div class="flex items-center gap-3">
                                        <div
                                            class="w-8 h-10 border-2 border-slate-300 rounded flex flex-col gap-1 p-1"
                                        >
                                            <div
                                                class="w-full h-2 bg-slate-300 rounded-sm"
                                            ></div>
                                            <div
                                                class="w-full h-1.5 bg-slate-200 rounded-sm"
                                            ></div>
                                            <div
                                                class="w-full h-4 bg-slate-200 rounded-sm"
                                            ></div>
                                        </div>
                                        <div>
                                            <div class="font-bold">
                                                Single Column <span
                                                    class="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full ml-1 font-medium"
                                                    >Recommended</span
                                                >
                                            </div>
                                            <div
                                                class="text-xs text-slate-500 mt-1"
                                            >
                                                Best for long CVs. ATS-friendly.
                                            </div>
                                        </div>
                                    </div>
                                </button>

                                <!-- Two Column -->
                                <button
                                    on:click={() => (modernLayout = "two")}
                                    class="flex-1 border-2 rounded-lg p-4 text-left transition-all
                                        {modernLayout === 'two'
                                        ? 'border-[#0369A1] bg-white shadow-sm ring-1 ring-[#0369A1]'
                                        : 'border-slate-300 bg-white/50 opacity-70 hover:opacity-100 hover:border-slate-400'}"
                                >
                                    <div class="flex items-center gap-3">
                                        <div
                                            class="w-8 h-10 border-2 border-slate-300 rounded flex gap-1 p-1"
                                        >
                                            <div
                                                class="w-1/3 h-full bg-slate-200 rounded-sm"
                                            ></div>
                                            <div
                                                class="w-2/3 flex flex-col gap-1"
                                            >
                                                <div
                                                    class="w-full h-2 bg-slate-300 rounded-sm"
                                                ></div>
                                                <div
                                                    class="w-full h-4 bg-slate-200 rounded-sm"
                                                ></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div class="font-bold">
                                                Two Column
                                            </div>
                                            <div
                                                class="text-xs text-slate-500 mt-1"
                                            >
                                                Classic side-by-side design.
                                            </div>
                                        </div>
                                    </div>
                                </button>
                            </div>
                        </div>
                    {/if}
                </div>

                <!-- Navigation -->
                <div class="flex justify-between pt-2">
                    <button
                        on:click={goBack}
                        class="px-5 py-2.5 border border-slate-300 text-slate-600 rounded-lg hover:bg-slate-50 transition-colors font-medium"
                    >
                        ← Back to Edit
                    </button>
                    <button
                        on:click={handleGenerate}
                        disabled={loading}
                        class="px-8 py-3 bg-gradient-to-r from-[#0369A1] to-[#0284C7] text-white rounded-lg font-bold shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {#if loading}
                            <div
                                class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"
                            ></div>
                            Generating…
                        {:else}
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
                                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                                />
                            </svg>
                            Download CV
                        {/if}
                    </button>
                </div>
            </div>
        {/if}
    </div>
</div>
