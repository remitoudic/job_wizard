<script lang="ts">
	import { onMount } from "svelte";
	import { fade } from "svelte/transition";
	import {
		parseJobUrl,
		generateCoverLetter,
		uploadImage,
		generatePdf,
		uploadContext,
		getAlternativeCoverLetter,
		API_URL,
	} from "$lib/api";

	let jobUrl = "";
	let userName = "";
	let imageFile: File | null = null;
	let imagePreview = "";
	let uploadedImageFilename = "";
	let contextText = "";
	let contextFilename = "";

	// Settings
	let showSettings = false;
	let templateStyle = "english";
	let language = "english"; // Currently unused backend-side but good for UI

	// Contact Info
	let email = "";
	let phone = "";
	let linkedin = "";
	let website = "";
	let address = "";
	let addressStreet = "";
	let addressPostcode = "";
	let addressCity = "";
	let addressCountry = "";
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

	// Edit Mode - Body
	let isEditing = false;
	let tempCoverLetter = "";

	// Edit Mode - Header
	let isEditingName = false;
	let isEditingDate = false;
	let isEditingSubject = false;

	let editableName = "";
	let editableDate = "";
	let editableSubject = "";

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
			if (result.address_street) addressStreet = result.address_street;
			if (result.address_postcode)
				addressPostcode = result.address_postcode;
			if (result.address_city) addressCity = result.address_city;
			if (result.address_country) addressCountry = result.address_country;

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

			// Initialize Editable Header Fields
			editableName =
				firstName || surname
					? `${firstName} ${surname}`.trim()
					: userName || "";
			editableDate = new Date().toLocaleDateString("en-US", {
				year: "numeric",
				month: "long",
				day: "numeric",
			});
			editableSubject = `Re: Application for ${jobData.title} at ${jobData.company}`;

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
				template_name: templateStyle,
				custom_date: editableDate,
				custom_subject: editableSubject,
				full_name: editableName,
				address,
				address_street: addressStreet,
				address_postcode: addressPostcode,
				address_city: addressCity,
				address_country: addressCountry,
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

		const fullUrl = `${API_URL}${pdfUrl}`;

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

		// Reset Edit Modes
		isEditing = false;
		isEditingName = false;
		isEditingDate = false;
		isEditingSubject = false;
		editableName = "";
		editableDate = "";
		editableSubject = "";
	}

	function startEditing() {
		tempCoverLetter = coverLetter;
		isEditing = true;
	}

	function saveEdit() {
		coverLetter = tempCoverLetter;
		isEditing = false;
		// Update the current version in the list too so switching doesn't lose it
		if (allCoverLetters[currentVersionIndex]) {
			allCoverLetters[currentVersionIndex].text = coverLetter;
		}
		invalidatePdf();
	}

	function cancelEdit() {
		isEditing = false;
		tempCoverLetter = "";
	}

	function toggleSettings() {
		showSettings = !showSettings;
	}

	// Close settings when clicking outside
	onMount(() => {
		const handleClickOutside = (event) => {
			const settingsMenu = document.getElementById("settings-menu");
			const settingsBtn = document.getElementById("settings-btn");
			if (
				showSettings &&
				settingsMenu &&
				settingsBtn &&
				!settingsMenu.contains(event.target) &&
				!settingsBtn.contains(event.target)
			) {
				showSettings = false;
			}
		};
		document.addEventListener("click", handleClickOutside);
		return () => document.removeEventListener("click", handleClickOutside);
	});
</script>

<svelte:head>
	<title>Job Wizard - AI Cover Letter Generator</title>
</svelte:head>

<div class="min-h-screen py-12 px-4">
	<div class="max-w-4xl mx-auto">
		<div class="text-center mb-12 relative">
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
			<div class="card relative">
				<div class="flex justify-between items-center mb-6">
					<h2 class="text-2xl font-bold text-gray-800">
						Your Cover Letter
					</h2>

					<!-- Settings Button -->
					<div class="relative inline-block text-left">
						<button
							id="settings-btn"
							on:click={toggleSettings}
							class="p-2 rounded-full hover:bg-gray-100 transition-colors text-gray-500 hover:text-primary-600 focus:outline-none"
							title="Generation Settings"
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
									d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
								/>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
								/>
							</svg>
						</button>

						<!-- Settings Menu -->
						{#if showSettings}
							<div
								id="settings-menu"
								class="absolute right-0 mt-2 w-64 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50 p-4"
								transition:fade
							>
								<div class="mb-4">
									<h3
										class="text-sm font-semibold text-gray-900 border-b pb-2 mb-3"
									>
										Generation Settings
									</h3>

									<div class="mb-4">
										<label
											class="block text-xs font-medium text-gray-700 mb-1"
										>
											Template Style
										</label>
										<select
											bind:value={templateStyle}
											on:change={invalidatePdf}
											class="block w-full pl-3 pr-10 py-2 text-sm border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
										>
											<option value="english"
												>English (Standard)</option
											>
											<option value="german"
												>German (DIN 5008)</option
											>
										</select>
									</div>

									<div>
										<label
											class="block text-xs font-medium text-gray-700 mb-1"
										>
											Language
										</label>
										<select
											bind:value={language}
											class="block w-full pl-3 pr-10 py-2 text-sm border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
										>
											<option value="english"
												>English</option
											>
											<!-- Future support: <option value="greek">Greek</option> -->
										</select>
									</div>
								</div>
							</div>
						{/if}
					</div>
				</div>

				<div
					class="bg-gray-50 rounded-lg p-12 mb-8 border-2 border-gray-200 shadow-sm"
				>
					<!-- Live Header Preview -->
					<div class="mb-8 font-serif">
						<!-- Line 1: Name -->
						<div
							class="text-base font-bold text-gray-900 mb-0.5 relative group w-fit"
						>
							{#if isEditingName}
								<div class="flex items-center space-x-2">
									<input
										type="text"
										bind:value={editableName}
										class="input py-1 px-2 text-base font-bold w-full"
									/>
									<button
										on:click={() => {
											isEditingName = false;
											invalidatePdf();
										}}
										class="p-1 text-green-600 hover:bg-green-50 rounded"
										title="Save"
									>
										✓
									</button>
									<button
										on:click={() => (isEditingName = false)}
										class="p-1 text-red-500 hover:bg-red-50 rounded"
										title="Cancel"
									>
										✕
									</button>
								</div>
							{:else}
								<div class="pr-8">
									{editableName || "[Your Name]"}
									<button
										on:click={() => (isEditingName = true)}
										class="absolute right-0 top-0.5 p-1 text-gray-400 hover:text-primary-600 opacity-0 group-hover:opacity-100 transition-opacity"
										title="Edit Name"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-4 w-4"
											viewBox="0 0 20 20"
											fill="currentColor"
										>
											<path
												d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
											/>
										</svg>
									</button>
								</div>
							{/if}
						</div>

						<!-- Line 2: Address -->
						<div class="text-base text-gray-900 mb-0.5">
							{#if addressStreet}
								{addressStreet}, {addressPostcode}
								{addressCity}
								{#if addressCountry}, {addressCountry}{/if}
							{:else if address}
								{address}
							{:else}
								<span class="text-gray-400 italic text-sm"
									>[Address not set]</span
								>
							{/if}
						</div>

						<!-- Line 3: Contact Info -->
						<div class="text-base text-gray-900 mb-6">
							{#if email}<span>{email}</span>{/if}
							{#if email && (phone || linkedin)}<span>
									|
								</span>{/if}
							{#if phone}<span>{phone}</span>{/if}
							{#if (email || phone) && linkedin}<span>
									|
								</span>{/if}
							{#if linkedin}<span>{linkedin}</span>{/if}
							{#if !email && !phone && !linkedin}
								<span class="text-gray-400 italic text-sm"
									>[Contact info not set]</span
								>
							{/if}
						</div>

						<div
							class="text-gray-800 mb-6 relative group w-fit ml-auto"
						>
							{#if isEditingDate}
								<div
									class="flex items-center space-x-2 justify-end"
								>
									<input
										type="text"
										bind:value={editableDate}
										class="input py-1 px-2 text-right w-48"
									/>
									<button
										on:click={() => {
											isEditingDate = false;
											invalidatePdf();
										}}
										class="p-1 text-green-600 hover:bg-green-50 rounded"
									>
										✓
									</button>
									<button
										on:click={() => (isEditingDate = false)}
										class="p-1 text-red-500 hover:bg-red-50 rounded"
									>
										✕
									</button>
								</div>
							{:else}
								<div class="pl-8">
									{editableDate || "[Date]"}
									<button
										on:click={() => (isEditingDate = true)}
										class="absolute -left-2 top-0 p-1 text-gray-400 hover:text-primary-600 opacity-0 group-hover:opacity-100 transition-opacity"
										title="Edit Date"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-4 w-4"
											viewBox="0 0 20 20"
											fill="currentColor"
										>
											<path
												d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
											/>
										</svg>
									</button>
								</div>
							{/if}
						</div>

						<div
							class="text-gray-800 mb-8 font-semibold relative group w-fit"
						>
							{#if isEditingSubject}
								<div class="flex items-center space-x-2">
									<input
										type="text"
										bind:value={editableSubject}
										class="input py-1 px-2 w-full font-semibold"
									/>
									<button
										on:click={() => {
											isEditingSubject = false;
											invalidatePdf();
										}}
										class="p-1 text-green-600 hover:bg-green-50 rounded"
									>
										✓
									</button>
									<button
										on:click={() =>
											(isEditingSubject = false)}
										class="p-1 text-red-500 hover:bg-red-50 rounded"
									>
										✕
									</button>
								</div>
							{:else}
								<div class="pr-8">
									{editableSubject || "[Subject]"}
									<button
										on:click={() =>
											(isEditingSubject = true)}
										class="absolute right-0 top-0 p-1 text-gray-400 hover:text-primary-600 opacity-0 group-hover:opacity-100 transition-opacity"
										title="Edit Subject"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-4 w-4"
											viewBox="0 0 20 20"
											fill="currentColor"
										>
											<path
												d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
											/>
										</svg>
									</button>
								</div>
							{/if}
						</div>
					</div>

					<!-- Content Area -->
					<div class="prose max-w-none font-serif">
						{#if isEditing}
							<textarea
								bind:value={tempCoverLetter}
								class="w-full h-96 p-4 border rounded-lg shadow-inner font-sans text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
							></textarea>
							<div class="flex justify-end space-x-3 mt-4">
								<button
									on:click={cancelEdit}
									class="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
								>
									Cancel
								</button>
								<button
									on:click={saveEdit}
									class="btn btn-primary"
								>
									Save Changes
								</button>
							</div>
						{:else}
							<div class="relative group">
								<button
									on:click={startEditing}
									class="absolute -top-2 -right-2 p-2 bg-white rounded-full shadow hover:shadow-md text-gray-400 hover:text-primary-600 opacity-0 group-hover:opacity-100 transition-all duration-200"
									title="Edit Text"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-5 w-5"
										viewBox="0 0 20 20"
										fill="currentColor"
									>
										<path
											d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
										/>
									</svg>
								</button>
								{#each coverLetter.split("\n\n") as paragraph}
									<p
										class="text-gray-800 mb-4 leading-relaxed whitespace-pre-line"
									>
										{paragraph}
									</p>
								{/each}
							</div>
						{/if}
					</div>
				</div>

				<!-- Contact Info Review / Edit Header -->
				<div class="mb-8">
					<details
						class="group bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm"
					>
						<summary
							class="flex justify-between items-center p-4 cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors list-none"
						>
							<h3 class="text-lg font-bold text-gray-800">
								📝 Edit Header
							</h3>
							<span
								class="text-gray-500 transform transition-transform duration-200 group-open:rotate-180"
								>▼</span
							>
						</summary>
						<div class="p-6 border-t border-gray-200 space-y-6">
							<!-- 1st line: first name, family name -->
							<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
								<div>
									<label
										class="block text-sm font-semibold text-gray-700 mb-1"
										>First Name</label
									>
									<input
										type="text"
										bind:value={firstName}
										on:input={invalidatePdf}
										placeholder="First Name"
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
								<div>
									<label
										class="block text-sm font-semibold text-gray-700 mb-1"
										>Family Name</label
									>
									<input
										type="text"
										bind:value={surname}
										on:input={invalidatePdf}
										placeholder="Family Name"
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
							</div>

							<!-- 2nd line: Adress street, postcode city country -->
							<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
								<div class="md:col-span-2">
									<label
										class="block text-sm font-semibold text-gray-700 mb-1"
										>Street</label
									>
									<input
										type="text"
										bind:value={addressStreet}
										on:input={invalidatePdf}
										placeholder="Street Address"
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
								<div>
									<label
										class="block text-sm font-semibold text-gray-700 mb-1"
										>Postcode</label
									>
									<input
										type="text"
										bind:value={addressPostcode}
										on:input={invalidatePdf}
										placeholder="Postcode"
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
								<div>
									<label
										class="block text-sm font-semibold text-gray-700 mb-1"
										>City & Country</label
									>
									<div class="flex space-x-2">
										<input
											type="text"
											bind:value={addressCity}
											on:input={invalidatePdf}
											placeholder="City"
											class="input"
											disabled={isPdfGenerating}
										/>
										<input
											type="text"
											bind:value={addressCountry}
											on:input={invalidatePdf}
											placeholder="Country"
											class="input"
											disabled={isPdfGenerating}
										/>
									</div>
								</div>
							</div>

							<!-- 3rd line: email address -->
							<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
								<div>
									<label
										class="block text-sm font-semibold text-gray-700 mb-1"
										>Email Address</label
									>
									<input
										type="email"
										bind:value={email}
										on:input={invalidatePdf}
										placeholder="email@example.com"
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
								<!-- Keep other fields as optional extras in this section if needed, or stick to the 3 lines -->
								<div class="grid grid-cols-2 gap-2">
									<div>
										<label
											class="block text-sm font-semibold text-gray-700 mb-1"
											>Phone</label
										>
										<input
											type="tel"
											bind:value={phone}
											on:input={invalidatePdf}
											placeholder="Phone"
											class="input"
											disabled={isPdfGenerating}
										/>
									</div>
									<div>
										<label
											class="block text-sm font-semibold text-gray-700 mb-1"
											>LinkedIn</label
										>
										<input
											type="text"
											bind:value={linkedin}
											on:input={invalidatePdf}
											placeholder="LinkedIn"
											class="input"
											disabled={isPdfGenerating}
										/>
									</div>
								</div>
							</div>
						</div>
					</details>
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
