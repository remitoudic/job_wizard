<script lang="ts">
	import { onMount } from "svelte";
	import {
		parseJobUrl,
		generateCoverLetter,
		uploadImage,
		generatePdf,
		uploadContext,
		getAlternativeCoverLetter,
	} from "$lib/api";

	let jobUrl = "";
	let userName = "";
	let imageFile: File | null = null;
	let imagePreview = "";
	let uploadedImageFilename = "";
	let contextText = "";
	let contextFilename = "";

	// Template
	let templateName = "generic";

	// Contact Info
	let email = "";
	let phone = "";
	let linkedin = "";
	let website = "";
	let address = "";
	let firstName = "";
	let surname = "";

	let jobData: any = null;
	let coverLetter = "";
	let pdfUrl = "";
	let downloaded = false;

	let isParsing = false;
	let isGenerating = false;
	let isPdfGenerating = false;
	let error = "";
	// Race Mode
	let step = 1;
	let alternativeId = "";
	let source = "";

	// Multiple cover letter versions
	let allCoverLetters: Array<{
		text: string;
		source: string;
		status?: string;
	}> = [];
	let currentVersionIndex = 0;
	let isLoadingAlternatives = false;

	async function handleParseJob(advance = true) {
		if (!jobUrl) {
			error = "Please enter a job URL";
			return;
		}

		isParsing = true;
		error = "";

		try {
			jobData = await parseJobUrl(jobUrl);
			if (advance) {
				step = 2;
				// Auto-start generation in background
				handleGenerateCoverLetter();
			}
		} catch (e: any) {
			error = e.message || "Failed to parse job URL";
		} finally {
			isParsing = false;
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

		isGenerating = true;
		error = "";

		try {
			const result = await generateCoverLetter({
				job_description: jobData,
				user_name: userName || "Applicant",
				context_text: contextText,
			});

			coverLetter = result.cover_letter;
			// Pre-fill contact info if available
			if (result.first_name) firstName = result.first_name;
			if (result.surname) surname = result.surname;
			if (result.email) email = result.email;
			if (result.phone) phone = result.phone;
			if (result.linkedin) linkedin = result.linkedin;
			if (result.website) website = result.website;
			if (result.address) address = result.address;

			// Auto-fill name if detected and currently empty
			if (result.user_name_detected && !userName) {
				userName = result.user_name_detected;
			}

			// Initialize all cover letters with the winner
			allCoverLetters = [
				{ text: result.cover_letter, source: result.source || "AI" },
			];
			currentVersionIndex = 0;

			// Capture race result
			if (result.alternative_id) alternativeId = result.alternative_id;
			if (result.source) source = result.source;

			// Load alternatives in background
			if (alternativeId) {
				loadAlternatives();
			}

			step = 3;
		} catch (e: any) {
			error = e.message || "Failed to generate cover letter";
		} finally {
			isGenerating = false;
		}
	}

	async function loadAlternatives() {
		if (!alternativeId || isLoadingAlternatives) return;

		isLoadingAlternatives = true;
		try {
			// Wait a bit for alternatives to complete
			await new Promise((resolve) => setTimeout(resolve, 2000));

			const altResult = await getAlternativeCoverLetter(alternativeId);
			if (altResult) {
				// altResult is now an array of alternatives
				if (Array.isArray(altResult)) {
					// Add all alternatives to the list
					altResult.forEach((alt) => {
						if (alt.text && alt.source) {
							allCoverLetters.push({
								text: alt.text,
								source: alt.source,
								status: alt.status || "completed",
							});
						}
					});
					allCoverLetters = allCoverLetters; // Trigger reactivity
				} else if (altResult.text) {
					// Single alternative (old format)
					allCoverLetters.push({
						text: altResult.text,
						source: altResult.source,
					});
					allCoverLetters = allCoverLetters;
				}
			}
		} catch (e) {
			console.log("Alternatives not ready yet, will retry...");
			// Retry after a delay
			setTimeout(() => loadAlternatives(), 3000);
		} finally {
			isLoadingAlternatives = false;
		}
	}

	function switchVersion(index: number) {
		if (index >= 0 && index < allCoverLetters.length) {
			currentVersionIndex = index;
			coverLetter = allCoverLetters[index].text;
			source = allCoverLetters[index].source;
			// Invalidate PDF when switching versions
			invalidatePdf();
		}
	}

	async function handleGeneratePdf() {
		if (!coverLetter || !jobData) return;

		isPdfGenerating = true;
		error = "";

		try {
			const result = await generatePdf({
				cover_letter: coverLetter,
				job_title: jobData.title,
				company: jobData.company,
				user_name: userName || "Applicant",
				first_name: firstName,
				surname: surname,
				image_filename: uploadedImageFilename,
				email,
				phone,
				linkedin,
				template_name: templateName,
			});

			pdfUrl = result.url;

			// Auto-download
			handleDownload();
		} catch (e: any) {
			error = e.message || "Failed to generate PDF";
		} finally {
			isPdfGenerating = false;
		}
	}

	function handleDownload() {
		if (!pdfUrl) return;

		const fullUrl = `http://localhost:8000${pdfUrl}`;

		// Create temporary link to force download
		const link = document.createElement("a");
		link.href = fullUrl;
		link.download = `Cover_Letter_${jobData.company.replace(/\s+/g, "_")}.pdf`; // Suggest a nice filename
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);

		// Update UI state
		setTimeout(() => {
			downloaded = true;
		}, 1000);
	}

	function invalidatePdf() {
		if (pdfUrl) {
			pdfUrl = "";
			downloaded = false;
		}
	}

	function reset() {
		jobUrl = "";
		userName = "";
		imageFile = null;
		imagePreview = "";
		uploadedImageFilename = "";
		contextText = "";
		contextFilename = "";
		firstName = "";
		surname = "";
		email = "";
		phone = "";
		linkedin = "";
		jobData = null;
		coverLetter = "";
		pdfUrl = "";
		downloaded = false;
		isParsing = false;
		isGenerating = false;
		isPdfGenerating = false;
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
				Generate personalized cover letters from just a url
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
					Enter Job URL
				</h2>

				<div class="space-y-6">
					<div>
						<input
							type="url"
							bind:value={jobUrl}
							placeholder="Paste job posting URL (LinkedIn, Indeed, etc)..."
							class="input"
							disabled={isParsing}
						/>

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

					<details
						class="group bg-white rounded-lg border border-gray-200 overflow-hidden"
					>
						<summary
							class="flex justify-between items-center p-4 cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors"
						>
							<h3 class="text-sm font-semibold text-gray-700">
								Add context to personalize your cover letter
							</h3>
							<span
								class="text-gray-500 transform transition-transform duration-200 group-open:rotate-180"
								>▼</span
							>
						</summary>
						<div class="p-4 border-t border-gray-200 space-y-6">
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
									disabled={isParsing}
								/>
							</div>

							<div>
								<label
									class="block text-sm font-semibold text-gray-700 mb-2"
								>
									Personalization (CV/PDF or Photo)
								</label>
								<p class="text-xs text-gray-500 mb-2">
									Upload a PDF (CV/Cover Letter) to
									personalize the content, OR an Image to
									appear on the PDF.
								</p>
								<input
									type="file"
									accept="image/*,.pdf"
									on:change={handleFileUpload}
									class="input"
									disabled={isParsing}
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
						</div>
					</details>

					<button
						on:click={() => handleParseJob(true)}
						disabled={isParsing || !jobUrl}
						class="btn btn-primary w-full"
					>
						{isParsing ? "Parsing..." : "Continue →"}
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
						disabled={isGenerating}
					>
						← Back
					</button>
					<button
						on:click={() =>
							coverLetter
								? (step = 3)
								: handleGenerateCoverLetter()}
						disabled={isGenerating}
						class="btn btn-primary flex-1 flex items-center justify-center"
					>
						{#if isGenerating}
							<svg
								class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
							Generating AI Draft...
						{:else if coverLetter}
							View Generated Letter →
						{:else}
							Generate Cover Letter ✨
						{/if}
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
					class="bg-gray-50 rounded-lg p-12 mb-8 border-2 border-gray-200 shadow-sm"
				>
					<!-- Live Header Preview -->
					<div class="mb-8 font-serif">
						<div class="text-xl font-bold text-gray-900 mb-2">
							{#if firstName || surname}
								{firstName} {surname}
							{:else}
								{userName || "Your Name"}
							{/if}
						</div>
						<div
							class="text-sm text-gray-600 mb-6 flex flex-wrap gap-3"
						>
							{#if email}<span>{email}</span>{/if}
							{#if email && (phone || linkedin)}<span>•</span
								>{/if}
							{#if phone}<span>{phone}</span>{/if}
							{#if (email || phone) && linkedin}<span>•</span
								>{/if}
							{#if linkedin}<span>{linkedin}</span>{/if}
						</div>

						<div class="text-gray-800 mb-6">
							{new Date().toLocaleDateString("en-US", {
								year: "numeric",
								month: "long",
								day: "numeric",
							})}
						</div>

						<div class="text-gray-800 mb-8 font-semibold">
							Re: Application for {jobData.title} at {jobData.company}
						</div>
					</div>

					<div class="prose max-w-none font-serif">
						{#each coverLetter.split("\n\n") as paragraph}
							<p
								class="text-gray-800 mb-4 leading-relaxed whitespace-pre-line"
							>
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
								>First Name</label
							>
							<input
								type="text"
								bind:value={firstName}
								on:input={invalidatePdf}
								placeholder="John"
								class="input text-sm"
								disabled={isPdfGenerating}
							/>
						</div>
						<div>
							<label
								class="block text-sm font-medium text-gray-700 mb-1"
								>Surname</label
							>
							<input
								type="text"
								bind:value={surname}
								on:input={invalidatePdf}
								placeholder="Doe"
								class="input text-sm"
								disabled={isPdfGenerating}
							/>
						</div>
						<div>
							<label
								class="block text-sm font-medium text-gray-700 mb-1"
								>Email</label
							>
							<input
								type="email"
								bind:value={email}
								on:input={invalidatePdf}
								placeholder="email@example.com"
								class="input text-sm"
								disabled={isPdfGenerating}
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
								on:input={invalidatePdf}
								placeholder="+1 234 567 8900"
								class="input text-sm"
								disabled={isPdfGenerating}
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
								on:input={invalidatePdf}
								placeholder="linkedin.com/in/..."
								class="input text-sm"
								disabled={isPdfGenerating}
							/>
						</div>

						<!-- New Fields -->
						<div>
							<label
								class="block text-sm font-medium text-gray-700 mb-1"
								>Website</label
							>
							<input
								type="text"
								bind:value={website}
								on:input={invalidatePdf}
								placeholder="portfolio.com"
								class="input text-sm"
								disabled={isPdfGenerating}
							/>
						</div>
						<!-- Address (Optional, maybe not full width?) -->
						<div class="md:col-span-2">
							<label
								class="block text-sm font-medium text-gray-700 mb-1"
								>Location / Address</label
							>
							<input
								type="text"
								bind:value={address}
								on:input={invalidatePdf}
								placeholder="New York, NY"
								class="input text-sm"
								disabled={isPdfGenerating}
							/>
						</div>
					</div>
				</div>

				<!-- Version Selector -->
				{#if allCoverLetters.length > 1}
					<div
						class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg"
					>
						<div class="flex items-center justify-between mb-3">
							<h3 class="text-sm font-semibold text-gray-700">
								🏁 Race Results - {allCoverLetters.length} Versions
								Generated
							</h3>
							{#if isLoadingAlternatives}
								<span class="text-xs text-gray-500"
									>Loading more...</span
								>
							{/if}
						</div>
						<div class="flex flex-wrap gap-2">
							{#each allCoverLetters as version, index}
								<button
									on:click={() => switchVersion(index)}
									disabled={version.status === "failed"}
									class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 {currentVersionIndex ===
									index
										? 'bg-primary-600 text-white shadow-md'
										: version.status === 'failed'
											? 'bg-red-50 text-red-500 border border-red-200 cursor-not-allowed'
											: 'bg-white text-gray-700 border border-gray-300 hover:border-primary-400 hover:bg-primary-50'}"
								>
									{#if index === 0}
										<span>🏆</span>
									{/if}
									{#if version.status === "failed"}
										<span>⚠️</span>
									{/if}
									<span>{version.source}</span>
									{#if version.status === "failed"}
										<span class="text-xs">(Failed)</span>
									{/if}
								</button>
							{/each}
						</div>
						<p class="text-xs text-gray-600 mt-2">
							Click to switch between versions. 🏆 = Race winner
							(fastest)
						</p>
					</div>
				{:else}
					<div class="flex justify-between items-center mb-6">
						<div class="text-sm text-gray-500 italic">
							Generated by {source || "AI"}
						</div>
						{#if isLoadingAlternatives}
							<span class="text-sm text-gray-500"
								>Loading alternatives...</span
							>
						{/if}
					</div>
				{/if}

				<div class="mb-6">
					<label class="block text-sm font-medium text-gray-700 mb-2"
						>PDF Template / Country</label
					>
					<select
						bind:value={templateName}
						on:change={invalidatePdf}
						class="input"
						disabled={isPdfGenerating}
					>
						<option value="generic">Generic (Standard)</option>
						<!-- Future templates can be added here -->
					</select>
				</div>

				<div class="space-y-4">
					{#if !pdfUrl}
						<button
							on:click={handleGeneratePdf}
							disabled={isPdfGenerating}
							class="btn btn-primary w-full"
						>
							{isPdfGenerating
								? "Generating PDF..."
								: "Download as PDF 📄"}
						</button>
					{:else if downloaded}
						<div
							class="flex flex-col items-center justify-center p-6 bg-green-50 rounded-lg border border-green-200 mb-4"
						>
							<div
								class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-3 shadow-sm"
							>
								<span class="text-3xl">✅</span>
							</div>
							<h3 class="text-xl font-bold text-green-800 mb-1">
								All Done!
							</h3>
							<p class="text-green-600 mb-4 text-center">
								Your cover letter has been downloaded to your
								<b>Downloads</b> folder.
							</p>
							<a
								href={`http://localhost:8000${pdfUrl}`}
								download
								class="text-green-700 font-medium hover:text-green-900 flex items-center transition-colors"
							>
								<span class="mr-1">⬇️</span> Download again
							</a>
						</div>
					{:else}
						<button
							on:click={handleDownload}
							class="btn btn-primary w-full block text-center"
						>
							Download PDF 📥
						</button>
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
