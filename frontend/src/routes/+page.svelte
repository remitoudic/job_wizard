<script lang="ts">
	import { onMount } from "svelte";
	import {
		parseJobUrl,
		generateCoverLetter,
		uploadImage,
		generatePdf,
		uploadContext,
	} from "$lib/api";

	let jobUrl = "";
	let userName = "";
	let userSkills = "";
	let imageFile: File | null = null;
	let imagePreview = "";
	let uploadedImageFilename = "";
	let contextText = "";
	let contextFilename = "";

	// Contact Info
	let email = "";
	let phone = "";
	let linkedin = "";

	let jobData: any = null;
	let coverLetter = "";
	let pdfUrl = "";

	let loading = false;
	let error = "";
	let step = 1; // 1: Input, 2: Review, 3: Result

	async function handleParseJob(advance = true) {
		if (!jobUrl) {
			error = "Please enter a job URL";
			return;
		}

		loading = true;
		error = "";

		try {
			jobData = await parseJobUrl(jobUrl);
			if (advance) step = 2;
		} catch (e: any) {
			error = e.message || "Failed to parse job URL";
		} finally {
			loading = false;
		}
	}

	async function handleFileUpload(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (file) {
			error = "";

			// Check if image or PDF
			if (file.type.startsWith("image/")) {
				imageFile = file;
				imagePreview = URL.createObjectURL(file);
				contextFilename = ""; // Clear context if switching to image

				try {
					const result = await uploadImage(file);
					uploadedImageFilename = result.filename;
				} catch (e: any) {
					error = "Failed to upload image";
				}
			} else if (file.type === "application/pdf") {
				// Handle PDF context
				imageFile = null;
				imagePreview = "";
				uploadedImageFilename = "";

				try {
					const result = await uploadContext(file);
					contextText = result.text;
					contextFilename = result.filename;
				} catch (e: any) {
					error = "Failed to upload and parse PDF context";
				}
			} else {
				error = "Please upload an image or PDF file";
			}
		}
	}

	async function handleGenerateCoverLetter() {
		if (!jobData) return;

		loading = true;
		error = "";

		try {
			const result = await generateCoverLetter({
				job_description: jobData,
				user_name: userName || "Applicant",
				user_skills: userSkills,
				context_text: contextText,
			});

			coverLetter = result.cover_letter;
			// Pre-fill contact info if available
			if (result.email) email = result.email;
			if (result.phone) phone = result.phone;
			if (result.linkedin) linkedin = result.linkedin;

			step = 3;
		} catch (e: any) {
			error = e.message || "Failed to generate cover letter";
		} finally {
			loading = false;
		}
	}

	async function handleGeneratePdf() {
		if (!coverLetter || !jobData) return;

		loading = true;
		error = "";

		try {
			const result = await generatePdf({
				cover_letter: coverLetter,
				job_title: jobData.title,
				company: jobData.company,
				user_name: userName || "Applicant",
				image_filename: uploadedImageFilename,
				email,
				phone,
				linkedin,
			});

			pdfUrl = result.url;
		} catch (e: any) {
			error = e.message || "Failed to generate PDF";
		} finally {
			loading = false;
		}
	}

	function reset() {
		jobUrl = "";
		userName = "";
		userSkills = "";
		imageFile = null;
		imagePreview = "";
		uploadedImageFilename = "";
		contextText = "";
		contextFilename = "";
		email = "";
		phone = "";
		linkedin = "";
		jobData = null;
		coverLetter = "";
		pdfUrl = "";
		error = "";
		step = 1;
	}
</script>

<svelte:head>
	<title>Job Wizard - AI Cover Letter Generator</title>
</svelte:head>

<div class="min-h-screen py-12 px-4">
	<div class="max-w-4xl mx-auto">
		<!-- Header -->
		<div class="text-center mb-12">
			<h1
				class="text-5xl font-bold bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent mb-4"
			>
				🧙‍♂️ Job Wizard
			</h1>
			<p class="text-xl text-gray-600">
				Generate personalized cover letters with AI
			</p>
		</div>

		<!-- Progress Steps -->
		<div class="flex justify-center mb-12">
			<div class="flex items-center space-x-4">
				<div class="flex items-center">
					<div
						class="w-10 h-10 rounded-full flex items-center justify-center font-semibold {step >=
						1
							? 'bg-primary-600 text-white'
							: 'bg-gray-300 text-gray-600'}"
					>
						1
					</div>
					<span
						class="ml-2 text-sm font-medium {step >= 1
							? 'text-primary-600'
							: 'text-gray-500'}">Job Details</span
					>
				</div>
				<div
					class="w-16 h-1 {step >= 2
						? 'bg-primary-600'
						: 'bg-gray-300'}"
				></div>
				<div class="flex items-center">
					<div
						class="w-10 h-10 rounded-full flex items-center justify-center font-semibold {step >=
						2
							? 'bg-primary-600 text-white'
							: 'bg-gray-300 text-gray-600'}"
					>
						2
					</div>
					<span
						class="ml-2 text-sm font-medium {step >= 2
							? 'text-primary-600'
							: 'text-gray-500'}">Generate</span
					>
				</div>
				<div
					class="w-16 h-1 {step >= 3
						? 'bg-primary-600'
						: 'bg-gray-300'}"
				></div>
				<div class="flex items-center">
					<div
						class="w-10 h-10 rounded-full flex items-center justify-center font-semibold {step >=
						3
							? 'bg-primary-600 text-white'
							: 'bg-gray-300 text-gray-600'}"
					>
						3
					</div>
					<span
						class="ml-2 text-sm font-medium {step >= 3
							? 'text-primary-600'
							: 'text-gray-500'}">Download</span
					>
				</div>
			</div>
		</div>

		<!-- Error Message -->
		{#if error}
			<div class="card mb-8 bg-red-50 border-2 border-red-200">
				<p class="text-red-700 font-medium">⚠️ {error}</p>
			</div>
		{/if}

		<!-- Step 1: Input -->
		{#if step === 1}
			<div class="card">
				<h2 class="text-2xl font-bold text-gray-800 mb-6">
					Enter Job Details
				</h2>

				<div class="space-y-6">
					<div>
						<label
							class="block text-sm font-semibold text-gray-700 mb-2"
						>
							Job URL
						</label>
						<input
							type="url"
							bind:value={jobUrl}
							placeholder="https://www.linkedin.com/jobs/view/..."
							class="input"
							disabled={loading}
						/>
						<p class="text-sm text-gray-500 mt-2">
							Paste a job posting URL from LinkedIn, Indeed, or
							other job boards
						</p>

						<div class="mt-3 flex space-x-3">
							<button
								on:click={() => handleParseJob(false)}
								disabled={loading || !jobUrl}
								class="btn btn-outline"
							>
								{loading ? "Parsing..." : "Parse Job Ad"}
							</button>
							<button
								on:click={() => handleParseJob(true)}
								disabled={loading || !jobUrl}
								class="btn btn-primary"
							>
								{loading ? "Parsing..." : "Continue →"}
							</button>
						</div>

						{#if jobData}
							<div class="mt-4 p-3 border rounded bg-gray-50">
								<div class="text-sm text-gray-500">
									Parsed preview
								</div>
								<div class="mt-2">
									<div class="font-medium text-gray-800">
										{jobData.title}
									</div>
									<div class="text-sm text-gray-600">
										{jobData.company}
									</div>
								</div>
							</div>
						{/if}
					</div>

					<div>
						<label
							class="block text-sm font-semibold text-gray-700 mb-2"
						>
							Your Name
						</label>
						<input
							type="text"
							bind:value={userName}
							placeholder="John Doe"
							class="input"
							disabled={loading}
						/>
					</div>

					<div>
						<label
							class="block text-sm font-semibold text-gray-700 mb-2"
						>
							Your Skills & Experience (Optional)
						</label>
						<textarea
							bind:value={userSkills}
							placeholder="E.g., 5 years of Python development, experience with FastAPI..."
							rows="4"
							class="input"
							disabled={loading}
						></textarea>
					</div>

					<div>
						<label
							class="block text-sm font-semibold text-gray-700 mb-2"
						>
							Personalization (CV/PDF or Photo)
						</label>
						<p class="text-xs text-gray-500 mb-2">
							Upload a PDF (CV/Cover Letter) to personalize the
							content, OR an Image to appear on the PDF.
						</p>
						<input
							type="file"
							accept="image/*,.pdf"
							on:change={handleFileUpload}
							class="input"
							disabled={loading}
						/>
						{#if imagePreview}
							<div class="mt-4">
								<img
									src={imagePreview}
									alt="Preview"
									class="w-32 h-32 object-cover rounded-lg shadow-md"
								/>
							</div>
						{/if}
						{#if contextFilename}
							<div
								class="mt-4 p-3 bg-blue-50 text-blue-700 rounded-lg flex items-center"
							>
								<span class="text-2xl mr-3">📄</span>
								<div>
									<div class="font-semibold">
										Context Loaded
									</div>
									<div class="text-sm opacity-75">
										Using info from uploaded PDF to
										personalize letter
									</div>
								</div>
							</div>
						{/if}
					</div>

					<button
						on:click={() => handleParseJob(true)}
						disabled={loading || !jobUrl}
						class="btn btn-primary w-full"
					>
						{loading ? "Parsing..." : "Continue →"}
					</button>
				</div>
			</div>
		{/if}

		<!-- Step 2: Review & Generate -->
		{#if step === 2 && jobData}
			<div class="card">
				<h2 class="text-2xl font-bold text-gray-800 mb-6">
					Review Job Details
				</h2>

				<div class="space-y-4 mb-8">
					<div>
						<h3
							class="text-sm font-semibold text-gray-500 uppercase"
						>
							Job Title
						</h3>
						<p class="text-lg font-medium text-gray-800">
							{jobData.title}
						</p>
					</div>
					<div>
						<h3
							class="text-sm font-semibold text-gray-500 uppercase"
						>
							Company
						</h3>
						<p class="text-lg font-medium text-gray-800">
							{jobData.company}
						</p>
					</div>
					<details
						class="group bg-white rounded-lg border border-gray-200 overflow-hidden mb-4"
					>
						<summary
							class="flex justify-between items-center p-4 cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors"
						>
							<h3
								class="text-sm font-semibold text-gray-500 uppercase"
							>
								Job Description
							</h3>
							<span
								class="text-gray-500 transform transition-transform duration-200"
								>▼</span
							>
						</summary>
						<div
							class="p-4 border-t border-gray-200 text-sm text-gray-700 whitespace-pre-wrap max-h-96 overflow-y-auto"
						>
							{jobData.description}
						</div>
					</details>

					{#if jobData.requirements.length > 0}
						<details
							class="group bg-white rounded-lg border border-gray-200 overflow-hidden"
						>
							<summary
								class="flex justify-between items-center p-4 cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors"
							>
								<h3
									class="text-sm font-semibold text-gray-500 uppercase"
								>
									Key Requirements
								</h3>
								<span
									class="text-gray-500 transform transition-transform duration-200"
									>▼</span
								>
							</summary>
							<div class="p-4 border-t border-gray-200">
								<ul class="list-disc list-inside space-y-1">
									{#each jobData.requirements as req}
										<li class="text-gray-700">{req}</li>
									{/each}
								</ul>
							</div>
						</details>
					{/if}

					{#if jobData.source}
						<div class="mt-4 text-sm text-gray-500">
							<span class="font-semibold">Source:</span>
							{jobData.source}
						</div>
					{/if}
				</div>

				<div class="flex space-x-4">
					<button
						on:click={() => (step = 1)}
						class="btn btn-secondary flex-1"
						disabled={loading}
					>
						← Back
					</button>
					<button
						on:click={handleGenerateCoverLetter}
						disabled={loading}
						class="btn btn-primary flex-1"
					>
						{loading ? "Generating..." : "Generate Cover Letter ✨"}
					</button>
				</div>
			</div>
		{/if}

		<!-- Step 3: Result -->
		{#if step === 3 && coverLetter}
			<div class="card">
				<h2 class="text-2xl font-bold text-gray-800 mb-6">
					Your Cover Letter
				</h2>

				<div
					class="bg-gray-50 rounded-lg p-6 mb-8 border-2 border-gray-200"
				>
					<div class="prose max-w-none">
						{#each coverLetter.split("\n\n") as paragraph}
							<p class="text-gray-800 mb-4 leading-relaxed">
								{paragraph}
							</p>
						{/each}
					</div>
				</div>

				<!-- Contact Info Review -->
				<div class="card mb-8 bg-white border border-gray-200">
					<h3 class="text-lg font-semibold text-gray-800 mb-4">
						Contact Information for Header
					</h3>
					<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
						<div>
							<label
								class="block text-sm font-medium text-gray-700 mb-1"
								>Email</label
							>
							<input
								type="email"
								bind:value={email}
								placeholder="email@example.com"
								class="input text-sm"
								disabled={loading || pdfUrl !== ""}
							/>
						</div>
						<div>
							<label
								class="block text-sm font-medium text-gray-700 mb-1"
								>Phone</label
							>
							<input
								type="tel"
								bind:value={phone}
								placeholder="+1 234 567 8900"
								class="input text-sm"
								disabled={loading || pdfUrl !== ""}
							/>
						</div>
						<div>
							<label
								class="block text-sm font-medium text-gray-700 mb-1"
								>LinkedIn/URL</label
							>
							<input
								type="text"
								bind:value={linkedin}
								placeholder="linkedin.com/in/..."
								class="input text-sm"
								disabled={loading || pdfUrl !== ""}
							/>
						</div>
					</div>
				</div>

				<div class="space-y-4">
					{#if !pdfUrl}
						<button
							on:click={handleGeneratePdf}
							disabled={loading}
							class="btn btn-primary w-full"
						>
							{loading
								? "Generating PDF..."
								: "Download as PDF 📄"}
						</button>
					{:else}
						<a
							href={`http://localhost:8000${pdfUrl}`}
							download
							class="btn btn-primary w-full block text-center"
						>
							Download PDF 📥
						</a>
					{/if}

					<button on:click={reset} class="btn btn-secondary w-full">
						Create Another Cover Letter
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.prose p {
		white-space: pre-wrap;
	}
</style>
