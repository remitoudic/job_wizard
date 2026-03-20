<script lang="ts">
	import { onMount } from "svelte";
	import { fade } from "svelte/transition";
	import { step } from "../stores/wizard";
	import {
		parseJobUrl,
		generateCoverLetter,
		uploadImage,
		generatePdf,
		uploadContext,
		getAlternativeCoverLetter,
		saveApplication,
		API_URL,
	} from "$lib/api";
	import { auth } from "../stores/auth";
	import SEO from "$lib/components/SEO.svelte";

	// SvelteKit automatically passes these props - declare them to avoid warnings
	export let data: any = {};

	let jobUrl = "";
	let userName = "";
	let imageFile: File | null = null;
	let imagePreview = "";
	let uploadedImageFilename = "";
	let contextText = "";
	let contextFilename = "";
	let customInstructions = "";

	// Settings
	let showSettings = false;
	// Single unified format selector: drives both template (PDF format) and language (AI writing)
	let selectedFormat: string = "british";
	$: templateName = selectedFormat;           // maps 1-to-1 to backend template_name
	$: language = selectedFormat === "german" ? "german" : "english";

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
	let originalCoverLetter = ""; // Store original to allow re-replacing name
	let pdfUrl = "";
	let downloaded = false;

	let isParsing = false;
	let isGenerating = false;
	let isPdfGenerating = false;
	let error = "";

	// Manual Input
	let isManualInput = false;
	let manualTitle = "";
	let manualCompany = "";
	let manualDescription = "";

	// Race Mode
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
		rawText: string; // Store original with [Your Name]
		source: string;
		status?: string;
	}> = [];
	let currentVersionIndex = 0;
	let isLoadingAlternatives = false;

	// Reactive: Replace [Your Name] placeholder with actual name
	// Function to replace [Your Name] placeholder with actual name
	// Function to replace [Your Name] placeholder with actual name
	function updateNameInCoverLetter() {
		// Use the raw text of the current version as source
		const currentVersion = allCoverLetters[currentVersionIndex];
		const sourceText = currentVersion
			? currentVersion.rawText
			: originalCoverLetter || coverLetter;

		if (sourceText && (firstName || surname)) {
			const fullName = `${firstName} ${surname}`.trim();
			if (fullName) {
				// Replace [Your Name] with actual name
				// Always do a fresh replacement from raw source
				// Try case-insensitive and optional brackets
				let newText = sourceText.replace(/\[?Your Name\]?/gi, fullName);

				// Fallback: If no replacement happened, try to find "Sincerely," and replace the line after
				if (
					newText === sourceText &&
					(newText.includes("Sincerely,") ||
						newText.includes("Best regards,"))
				) {
					// Regex to find Sincerely, followed by newlines and then ANY text to the end or double newline
					// This assumes the signature is the last thing or separated
					newText = newText.replace(
						/(Sincerely,|Best regards,)\s+[\s\S]+?$/i,
						`$1\n\n${fullName}`,
					);
				}

				// Always update editableName for the header preview
				editableName = fullName;

				// Only update body if it changed (e.g. placeholder found and replaced)
				if (newText !== coverLetter) {
					coverLetter = newText;

					// Update the current version in the list too (processed text)
					if (allCoverLetters[currentVersionIndex]) {
						allCoverLetters[currentVersionIndex].text = coverLetter;
					}
					invalidatePdf();
				}
			}
		}
	}

	async function handleParseJob(advance = true) {
		jobUrl = jobUrl.trim();
		if (!jobUrl) {
			error = "Please enter a job URL";
			return;
		}

		isParsing = true;
		error = "";
		isManualInput = false;

		try {
			jobData = await parseJobUrl(jobUrl);
			if (advance) {
				step.set(2);
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
				custom_instructions: customInstructions,
				language,
			});

			// Initialize
			coverLetter = result.cover_letter;
			originalCoverLetter = result.cover_letter; // Save original

			// Initialize all cover letters with the winner
			allCoverLetters = [
				{
					text: result.cover_letter,
					rawText: result.cover_letter,
					source: result.source || "AI",
				},
			];
			currentVersionIndex = 0;

			// Auto-replace name if already entered
			if (firstName || surname) {
				// This acts on currentVersionIndex 0
				updateNameInCoverLetter();
				// updateNameInCoverLetter updates 'coverLetter' and 'allCoverLetters[0].text'
			}

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

			// Capture race result
			if (result.alternative_id) alternativeId = result.alternative_id;
			if (result.source) source = result.source;

			// Load alternatives in background
			if (alternativeId) {
				isLoadingAlternatives = true;
				loadAlternatives();
			}

			// Initialize Editable Header Fields
			editableName =
				firstName || surname
					? `${firstName} ${surname}`.trim()
					: userName || "";

			// Date and subject adapt to selected language/format
			if (language === "german") {
				const now = new Date();
				const deMonths = [
					"Januar", "Februar", "März", "April", "Mai", "Juni",
					"Juli", "August", "September", "Oktober", "November", "Dezember"
				];
				editableDate = `${now.getDate()}. ${deMonths[now.getMonth()]} ${now.getFullYear()}`;
				editableSubject = `Bewerbung als ${jobData.title}`;
			} else {
				editableDate = new Date().toLocaleDateString("en-GB", {
					year: "numeric",
					month: "long",
					day: "numeric",
				});
				editableSubject = `Re: Application for ${jobData.title} at ${jobData.company}`;
			}

			step.set(3);
		} catch (e: any) {
			error = e.message || "Failed to generate cover letter";
		} finally {
			isGenerating = false;
		}
	}

	async function loadAlternatives() {
		if (!alternativeId) return;

		// Don't set isLoadingAlternatives globally if we want silent updates
		// But for first load we might want it.
		// Let's keep it simple.

		try {
			const altResult = await getAlternativeCoverLetter(alternativeId);

			if (altResult) {
				let newAlternatives = [];
				let isComplete = true;

				// Handle new format { status, alternatives }
				if (
					altResult.alternatives &&
					Array.isArray(altResult.alternatives)
				) {
					newAlternatives = altResult.alternatives;
					isComplete = altResult.status === "completed";
				}
				// Handle legacy array format (just in case)
				else if (Array.isArray(altResult)) {
					newAlternatives = altResult;
					isComplete = true; // Assume complete if legacy array
				}
				// Handle legacy single object
				else if (altResult.text) {
					newAlternatives = [altResult];
					isComplete = true;
				}

				// Process alternatives
				// Clear existing and replace, or generic update.
				// Replacing is safest for now to ensure we have latest status of each.
				// We want to preserve the selection if possible potentially, or just rebuild.

				// We need to map them to the UI structure
				const mapped: any[] = [];

				// Keep the winner (first one in allCoverLetters) if it's there
				if (allCoverLetters.length > 0) {
					mapped.push(allCoverLetters[0]);
				}

				newAlternatives.forEach((alt: any) => {
					// Check if it's already the winner?
					// The backend alternatives list MIGHT contain the winner if logic changed,
					// but typically it contains "finished alternatives".
					// LLMService now puts all non-winner results into alternatives.

					// Add if not duplicate (checks source)
					if (!mapped.some((m) => m.source === alt.source)) {
						mapped.push({
							text: alt.text,
							rawText: alt.text, // Assume incoming is raw
							source: alt.source,
							status: alt.status || "completed",
						});
					}
				});

				// Re-apply current name if we have loaded new ones
				// But we need to be careful not to overwrite user edits if we were editing?
				// For now, let's assume rawText is source of truth.

				// Update list
				allCoverLetters = mapped;

				// If we have a name set, re-run update for current index to ensure it's processed
				if (firstName || surname) {
					updateNameInCoverLetter();
				}

				if (!isComplete) {
					// Poll again
					setTimeout(() => loadAlternatives(), 2000);
				} else {
					isLoadingAlternatives = false;
				}
			}
		} catch (e) {
			console.log("Error loading alternatives or not ready:", e);
			// Retry on error too (maybe 404 not ready yet)
			setTimeout(() => loadAlternatives(), 3000);
		}
	}

	function switchVersion(index: number) {
		if (index >= 0 && index < allCoverLetters.length) {
			currentVersionIndex = index;

			// Start with raw text
			coverLetter = allCoverLetters[index].rawText;
			source = allCoverLetters[index].source;

			// If we have name set, apply it immediately
			if (firstName || surname) {
				// This function uses currentVersionIndex and updates coverLetter and allCoverLetters[i].text
				updateNameInCoverLetter();
			} else {
				// Just update text
				allCoverLetters[index].text = coverLetter;
			}

			// Invalidate PDF when switching versions
			invalidatePdf();
		}
	}

	function handleManualSubmit() {
		if (!manualTitle || !manualCompany || !manualDescription) {
			error = "Please fill in all manual fields";
			return;
		}
		error = "";
		jobData = {
			title: manualTitle,
			company: manualCompany,
			description: manualDescription,
			requirements: [],
			url: jobUrl || "manual",
		};
		step.set(2);
		handleGenerateCoverLetter();
	}

	async function handleGeneratePdf() {
		if (!coverLetter || !jobData) return;

		isPdfGenerating = true;
		error = "";

		try {
			// preparing header object
			const header = {
				name: userName,
				email,
				phone,
				linkedin,
				address,
				address_street: addressStreet,
				address_postcode: addressPostcode,
				address_city: addressCity,
				address_country: addressCountry,
			};

			// Saving application to database
			// Saving application to database (only if logged in)
			if ($auth.isAuthenticated) {
				try {
					await saveApplication({
						job_url: jobUrl,
						job_title: jobData.title,
						job_company: jobData.company,
						job_description:
							jobData.full_description || jobData.description, // Use full description if available
						job_requirements: jobData.requirements,
						job_source: jobData.source || "unknown",
						generated_letters: allCoverLetters.map((l) => ({
							model: l.source.includes("GPT")
								? "gpt-4o"
								: "llama-3.2-1b", // precise mapping if possible, else approximation
							letter: l.text,
							timestamp: new Date().toISOString(), // API expects this
						})),
						selected_letter_index: currentVersionIndex,
						header: header,
						cover_letter_body: coverLetter,
					});
				} catch (err) {
					console.warn("Failed to save application to history:", err);
					// Continue to PDF generation even if save fails
				}
			}

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

	async function handleDownload() {
		if (!pdfUrl) return;

		// Check if it's a static upload path or API endpoint
		const fullUrl = pdfUrl.startsWith("/uploads/")
			? `${window.location.origin}${pdfUrl}`
			: `${API_URL}${pdfUrl}`;

		try {
			// Fetch blob to enforce filename
			const response = await fetch(fullUrl);
			const blob = await response.blob();
			const blobUrl = window.URL.createObjectURL(blob);

			const link = document.createElement("a");
			link.href = blobUrl;
			const company = jobData.company
				? jobData.company.replace(/[^a-zA-Z0-9]/g, "_")
				: "Company";
			const name =
				firstName || surname
					? `${firstName}_${surname}`.replace(/[^a-zA-Z0-9_]/g, "_")
					: (userName || "Applicant").replace(/[^a-zA-Z0-9_]/g, "_");
			const date = new Date().toISOString().split("T")[0]; // YYYY-MM-DD

			link.download = `cover_letter_${company}_${name}_${date}.pdf`;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);

			// Cleanup
			window.URL.revokeObjectURL(blobUrl);

			// Update UI state
			setTimeout(() => {
				downloaded = true;
			}, 1000);
		} catch (e) {
			console.error("Download failed:", e);
			// Fallback to direct link if fetch fails
			window.open(fullUrl, "_blank");
		}
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
		customInstructions = "";
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
		step.set(1);

		// Reset format selection
		selectedFormat = "british";
		manualTitle = "";
		manualCompany = "";
		manualDescription = "";

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
		const handleClickOutside = (event: MouseEvent) => {
			const settingsMenu = document.getElementById("settings-menu");
			const settingsBtn = document.getElementById("settings-btn");
			if (
				showSettings &&
				settingsMenu &&
				settingsBtn &&
				!settingsMenu.contains(event.target as Node) &&
				!settingsBtn.contains(event.target as Node)
			) {
				showSettings = false;
			}
		};
		document.addEventListener("click", handleClickOutside);
		return () => document.removeEventListener("click", handleClickOutside);
	});
</script>

<SEO
	title="Vite a Job - AI Cover Letter Generator"
	description="Learn how to write a cover letter that beats the ATS. Our AI-powered generator creates professional, personalized applications in seconds to help you get more interviews."
/>

<div class="min-h-screen py-16 px-4">
	<div class="max-w-3xl mx-auto">
		<div class="text-center mb-16 px-4">
			<h1
				class="text-5xl font-extrabold text-[#0F172A] tracking-tight mb-4"
			>
				Vite a Job
			</h1>
			<p class="text-lg text-[#334155] max-w-lg mx-auto leading-relaxed">
				Craft professional, personalized cover letters in seconds. Just
				paste a LinkedIn job URL and let AI do the heavy lifting.
			</p>
		</div>

		<!-- Progress Steps -->
		<div class="flex justify-center mb-16">
			<div class="flex items-center w-full max-w-md">
				<div class="flex flex-col items-center flex-1 relative">
					<button
						class="w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all {$step >=
						1
							? 'bg-[#0369A1] text-white shadow-sm'
							: 'bg-[#E2E8F0] text-[#64748B]'} cursor-pointer hover:bg-[#0284C7]"
						on:click={() => step.set(1)}
					>
						1
					</button>
					<span
						class="mt-2 text-xs font-semibold uppercase tracking-wider {$step >=
						1
							? 'text-[#0369A1]'
							: 'text-[#64748B]'}">Details</span
					>
				</div>
				<div
					class="w-20 h-0.5 {$step >= 2
						? 'bg-[#0369A1]'
						: 'bg-[#E2E8F0]'} -mt-6"
				></div>
				<div class="flex flex-col items-center flex-1 relative">
					<button
						class="w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all {$step >=
						2
							? 'bg-[#0369A1] text-white shadow-sm'
							: 'bg-[#E2E8F0] text-[#64748B]'} {jobData
							? 'cursor-pointer hover:bg-[#0284C7]'
							: 'cursor-default'}"
						on:click={() => {
							if (jobData) step.set(2);
						}}
					>
						2
					</button>
					<span
						class="mt-2 text-xs font-semibold uppercase tracking-wider {$step >=
						2
							? 'text-[#0369A1]'
							: 'text-[#64748B]'}">Review</span
					>
				</div>
				<div
					class="w-20 h-0.5 {$step >= 3
						? 'bg-[#0369A1]'
						: 'bg-[#E2E8F0]'} -mt-6"
				></div>
				<div class="flex flex-col items-center flex-1 relative">
					<button
						class="w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all {$step >=
						3
							? 'bg-[#0369A1] text-white shadow-sm'
							: 'bg-[#E2E8F0] text-[#64748B]'} {coverLetter
							? 'cursor-pointer hover:bg-[#0284C7]'
							: 'cursor-default'}"
						on:click={() => {
							if (coverLetter) step.set(3);
						}}
					>
						3
					</button>
					<span
						class="mt-2 text-xs font-semibold uppercase tracking-wider {$step >=
						3
							? 'text-[#0369A1]'
							: 'text-[#64748B]'}">Result</span
					>
				</div>
			</div>
		</div>

		<!-- Error Message -->
		{#if error}
			<div
				class="mb-8 p-4 bg-red-50 border border-red-100 text-red-700 rounded-md text-sm flex flex-col gap-4"
			>
				<div class="flex items-start gap-3">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5 text-red-500 shrink-0"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
						/>
					</svg>
					<span class="flex-1">{error}</span>
				</div>

				{#if error}
					<div class="pl-8">
						<button
							on:click={() => {
								isManualInput = true;
								error = "";
							}}
							class="text-[#0369A1] font-semibold hover:underline flex items-center gap-1.5 transition-all"
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
									d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
								/>
							</svg>
							Enter details manually
						</button>
					</div>
				{/if}
			</div>
		{/if}

		{#if isManualInput && $step === 1}
			<div
				class="card mb-8 animate-in fade-in slide-in-from-top-4 duration-300"
				transition:fade
			>
				<div class="mb-6 flex justify-between items-center">
					<div>
						<h2 class="text-xl font-bold text-[#0F172A]">
							Manual Job Entry
						</h2>
						<p class="text-[#64748B] text-xs">
							The site is blocked, but we can still help if you
							paste the details.
						</p>
					</div>
					<button
						on:click={() => (isManualInput = false)}
						class="text-[#64748B] hover:text-[#0F172A] p-1"
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
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
				</div>

				<div class="space-y-5">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label
								for="manual-title"
								class="block text-xs font-bold uppercase tracking-wider text-[#64748B] mb-2"
								>Job Title</label
							>
							<input
								id="manual-title"
								type="text"
								bind:value={manualTitle}
								class="input text-sm"
								placeholder="e.g. Senior Software Engineer"
							/>
						</div>
						<div>
							<label
								for="manual-company"
								class="block text-xs font-bold uppercase tracking-wider text-[#64748B] mb-2"
								>Company Name</label
							>
							<input
								id="manual-company"
								type="text"
								bind:value={manualCompany}
								class="input text-sm"
								placeholder="e.g. Acme Corp"
							/>
						</div>
					</div>
					<div>
						<label
							for="manual-desc"
							class="block text-xs font-bold uppercase tracking-wider text-[#64748B] mb-2"
							>Job Description</label
						>
						<textarea
							id="manual-desc"
							bind:value={manualDescription}
							rows="8"
							class="input text-sm resize-none"
							placeholder="Paste the full job description here..."
						></textarea>
					</div>
					<button
						on:click={handleManualSubmit}
						class="btn btn-primary w-full py-3 font-semibold shadow-lg hover:shadow-xl transition-all"
					>
						Submit & Generate Letter
					</button>
				</div>
			</div>
		{/if}

		<!-- Step 1: Input -->
		{#if $step === 1}
			<div class="card">
				<div class="mb-8">
					<h2 class="text-2xl font-bold text-[#0F172A] mb-2">
						Get Started
					</h2>
					<p class="text-[#334155] text-sm">
						Paste the link to the job posting below.
					</p>
				</div>

				<div class="space-y-8">
					<div class="relative">
						<input
							type="url"
							bind:value={jobUrl}
							placeholder="e.g. https://www.linkedin.com/jobs/view/..."
							class="input pr-12"
							disabled={isParsing}
						/>
						{#if isParsing}
							<div
								class="absolute right-4 top-1/2 -translate-y-1/2"
							>
								<svg
									class="animate-spin h-5 w-5 text-[#0369A1]"
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
							</div>
						{/if}

						{#if jobData}
							<div
								class="mt-4 p-4 rounded-md border border-[#E2E8F0] bg-[#F8FAFC] flex items-center justify-between"
							>
								<div>
									<div
										class="text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-1"
									>
										Parsed Position
									</div>
									<div class="font-semibold text-[#0F172A]">
										{jobData.title}
									</div>
									<div class="text-sm text-[#334155]">
										{jobData.company}
									</div>
								</div>
								<div class="bg-green-100 p-1.5 rounded-full">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-5 w-5 text-green-600"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
										/>
									</svg>
								</div>
							</div>
						{/if}
					</div>

					<div class="pt-2 border-t border-[#E2E8F0]">
						<details class="group">
							<summary
								class="flex justify-between items-center py-4 cursor-pointer text-[#334155] hover:text-[#0F172A] transition-colors focus:outline-none"
							>
								<span class="text-sm font-semibold"
									>Personalize your letter</span
								>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-5 w-5 transition-transform duration-200 group-open:rotate-180"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M19 9l-7 7-7-7"
									/>
								</svg>
							</summary>
							<div
								class="pb-6 space-y-6 animate-in fade-in slide-in-from-top-2"
							>
								<div>
									<label
										for="letter-language"
										class="block text-sm font-semibold text-[#334155] mb-2"
										>Cover Letter Language</label
									>
									<p class="text-xs text-[#64748B] mb-3">
										Choose the language for the generated cover letter.
									</p>
									<select
										id="letter-language"
										bind:value={language}
										class="w-full px-4 py-3 rounded-lg border border-[#E2E8F0] bg-white text-[#0F172A] focus:border-[#0369A1] focus:ring-2 focus:ring-[#0369A1]/20 outline-none transition-all text-sm mb-6"
									>
										<option value="english">English</option>
										<option value="german">German</option>
									</select>
								</div>

								<div>
									<label
										for="custom-instructions"
										class="block text-sm font-semibold text-[#334155] mb-2"
										>Custom Guidance</label
									>
									<p class="text-xs text-[#64748B] mb-3">
										Add specific instructions for the AI
										(e.g., "Focus on my leadership
										experience").
									</p>
									<textarea
										id="custom-instructions"
										bind:value={customInstructions}
										placeholder="Optional: Enter custom instructions here..."
										class="w-full px-4 py-3 rounded-lg border border-[#E2E8F0] focus:border-[#0369A1] focus:ring-2 focus:ring-[#0369A1]/20 outline-none transition-all resize-y min-h-[80px] text-sm"
									></textarea>
								</div>

								<div>
									<label
										for="file-upload-section"
										class="block text-sm font-semibold text-[#334155] mb-2"
										>Upload info</label
									>
									<p class="text-xs text-[#64748B] mb-3">
										Upload information about yourself so
										that we can personalize your cover
										letter (for example, your CV).
									</p>
									<div class="flex items-center gap-4">
										<input
											type="file"
											id="file-upload-section"
											accept="image/*,.pdf"
											on:change={handleFileUpload}
											class="hidden"
											disabled={isParsing}
										/>
										<label
											for="file-upload"
											class="btn btn-secondary text-sm cursor-pointer flex items-center gap-2"
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
													d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
												/>
											</svg>
											Choose File
										</label>
										{#if imageFile || contextFilename}
											<span
												class="text-sm font-medium text-green-600 flex items-center gap-1"
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
														d="M5 13l4 4L19 7"
													/>
												</svg>
												{imageFile ? "Image" : "PDF"} Selected
											</span>
										{/if}
									</div>

									{#if imagePreview}
										<div
											class="mt-4 inline-block p-1 border border-[#E2E8F0] rounded-lg"
										>
											<img
												src={imagePreview}
												alt="Preview"
												class="w-24 h-24 object-cover rounded-md"
											/>
										</div>
									{/if}
								</div>
							</div>
						</details>
					</div>

					<button
						on:click={() => {
							// If we already have jobData for this URL, just go to Step 2
							// We can check if jobData exists and loosely if the URL matches (if we want to be strict)
							if (jobData) {
								step.set(2);
							} else {
								handleParseJob(true);
							}
						}}
						disabled={isParsing || !jobUrl}
						class="btn btn-primary w-full py-4 text-lg"
					>
						{isParsing ? "Analyzing Position..." : "Next Step"}
					</button>
				</div>
			</div>
		{/if}

		<!-- Step 2: Review & Generate -->
		{#if $step === 2 && jobData}
			<div class="card">
				<div class="mb-8">
					<h2 class="text-2xl font-bold text-[#0F172A] mb-2">
						Review Position
					</h2>
					<p class="text-[#334155] text-sm">
						Verify the details before generating your letter.
					</p>
				</div>

				<div class="space-y-6 mb-10">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
						<div
							class="p-4 rounded-md bg-[#F8FAFC] border border-[#E2E8F0]"
						>
							<h3
								class="text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-1"
							>
								Role
							</h3>
							<p class="text-lg font-bold text-[#0F172A]">
								{jobData.title}
							</p>
						</div>
						<div
							class="p-4 rounded-md bg-[#F8FAFC] border border-[#E2E8F0]"
						>
							<h3
								class="text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-1"
							>
								Company
							</h3>
							<p class="text-lg font-bold text-[#0F172A]">
								{jobData.company}
							</p>
						</div>
					</div>

					<details
						class="group border border-[#E2E8F0] rounded-md overflow-hidden transition-all"
					>
						<summary
							class="flex justify-between items-center p-4 cursor-pointer bg-white hover:bg-[#F8FAFC] transition-colors focus:outline-none"
						>
							<span class="text-sm font-semibold text-[#334155]"
								>Full Job Description</span
							>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5 transition-transform duration-200 group-open:rotate-180"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 9l-7 7-7-7"
								/>
							</svg>
						</summary>
						<div
							class="p-6 border-t border-[#E2E8F0] text-sm text-[#334155] leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto bg-white"
						>
							{jobData.description}
						</div>
					</details>

					{#if jobData.requirements.length > 0}
						<details
							class="group border border-[#E2E8F0] rounded-md overflow-hidden transition-all bg-white"
						>
							<summary
								class="flex justify-between items-center p-4 cursor-pointer hover:bg-[#F8FAFC] transition-colors focus:outline-none list-none"
							>
								<span
									class="text-[10px] font-bold uppercase tracking-wider text-[#64748B]"
								>
									Key Requirements Detected
								</span>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-5 w-5 text-[#64748B] transition-transform duration-200 group-open:rotate-180"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M19 9l-7 7-7-7"
									/>
								</svg>
							</summary>
							<div class="p-6 border-t border-[#E2E8F0]">
								<div
									class="grid grid-cols-1 sm:grid-cols-2 gap-3"
								>
									{#each jobData.requirements as req}
										<div
											class="flex items-start gap-2 text-sm text-[#334155]"
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="h-4 w-4 text-[#0369A1] shrink-0 mt-0.5"
												fill="none"
												viewBox="0 0 24 24"
												stroke="currentColor"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M5 13l4 4L19 7"
												/>
											</svg>
											<span>{req}</span>
										</div>
									{/each}
								</div>
							</div>
						</details>
					{/if}
				</div>

				<div class="flex flex-col sm:flex-row gap-4">
					<button
						on:click={() => step.set(1)}
						class="btn btn-secondary sm:flex-1 py-4"
						disabled={isGenerating}
					>
						Back
					</button>
					<button
						on:click={() =>
							coverLetter
								? step.set(3)
								: handleGenerateCoverLetter()}
						disabled={isGenerating}
						class="btn btn-primary sm:flex-[2] py-4 flex items-center justify-center gap-3"
					>
						{#if isGenerating}
							<svg
								class="animate-spin h-5 w-5 text-white"
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
							Crafting Your Letter...
						{:else if coverLetter}
							Review Draft
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
									d="M13 10V3L4 14h7v7l9-11h-7z"
								/>
							</svg>
							Generate Cover Letter
						{/if}
					</button>
				</div>
			</div>
		{/if}

		<!-- Step 3: Result -->
		{#if $step === 3 && coverLetter}
			<div class="card relative">
				<div
					class="flex justify-between items-end mb-8 border-b border-[#E2E8F0] pb-6"
				>
					<div>
						<h2 class="text-2xl font-bold text-[#0F172A] mb-1">
							Your Cover Letter
						</h2>
						<p class="text-[#334155] text-sm">
							Review, edit, and download your personalized draft.
						</p>
					</div>

					<div class="relative">
						<button
							id="settings-btn"
							on:click={toggleSettings}
							class="p-2.5 rounded-md hover:bg-[#F1F5F9] transition-colors text-[#64748B] hover:text-[#0369A1] focus:outline-none border border-[#E2E8F0]"
							title="Letter Settings"
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
									d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
								/>
							</svg>
						</button>

						{#if showSettings}
							<div
								id="settings-menu"
								class="absolute right-0 mt-3 w-72 rounded-lg shadow-xl bg-white ring-1 ring-[#0F172A] ring-opacity-5 z-50 p-6 animate-in fade-in zoom-in-95"
								transition:fade
							>
								<h3
									class="text-sm font-bold text-[#0F172A] mb-4"
								>
									Letter Preferences
								</h3>

								<div class="space-y-4">
									<div>
										<span
											class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
											>Language &amp; Format</span
										>
										<p class="text-[11px] text-[#94A3B8] mb-3 leading-relaxed">
											Sets the AI writing language and PDF formatting standard.
										</p>
										<div class="flex flex-col gap-2">
											<button
												id="format-british"
												type="button"
												on:click={() => { selectedFormat = "british"; invalidatePdf(); }}
												class="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg border text-left transition-all {selectedFormat === 'british'
													? 'border-[#0369A1] bg-[#EFF6FF] text-[#0369A1]'
													: 'border-[#E2E8F0] bg-white text-[#334155] hover:bg-[#F8FAFC]'}"
											>
												<span class="text-xl leading-none select-none">🇬🇧</span>
												<div class="flex-1 min-w-0">
													<div class="text-sm font-semibold leading-tight">British English</div>
													<div class="text-[11px] text-[#64748B] mt-0.5">Standard business format</div>
												</div>
												{#if selectedFormat === 'british'}
													<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-[#0369A1] shrink-0" viewBox="0 0 20 20" fill="currentColor">
														<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
													</svg>
												{/if}
											</button>
											<button
												id="format-german"
												type="button"
												on:click={() => { selectedFormat = "german"; invalidatePdf(); }}
												class="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg border text-left transition-all {selectedFormat === 'german'
													? 'border-[#0369A1] bg-[#EFF6FF] text-[#0369A1]'
													: 'border-[#E2E8F0] bg-white text-[#334155] hover:bg-[#F8FAFC]'}"
											>
												<span class="text-xl leading-none select-none">🇩🇪</span>
												<div class="flex-1 min-w-0">
													<div class="text-sm font-semibold leading-tight">Deutsch</div>
													<div class="text-[11px] text-[#64748B] mt-0.5">DIN 5008 · Bewerbungsschreiben</div>
												</div>
												{#if selectedFormat === 'german'}
													<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-[#0369A1] shrink-0" viewBox="0 0 20 20" fill="currentColor">
														<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
													</svg>
												{/if}
											</button>
										</div>
									</div>
								</div>
							</div>
						{/if}
					</div>
				</div>

				<div
					class="bg-[#F8FAFC] rounded-lg p-8 md:p-12 mb-10 border border-[#E2E8F0] shadow-inner relative overflow-hidden"
				>
					<div
						class="absolute top-0 left-0 w-1 h-full bg-[#0369A1]/20"
					></div>
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
					<div class="prose max-w-none font-serif relative">
						{#if isEditing}
							<textarea
								bind:value={tempCoverLetter}
								class="w-full h-96 p-6 border border-[#0369A1] rounded-md bg-white font-serif text-lg leading-relaxed focus:ring-4 focus:ring-[#0369A1]/10 outline-none transition-all"
							></textarea>
							<div class="flex justify-end gap-3 mt-6">
								<button
									on:click={cancelEdit}
									class="px-4 py-2 text-sm font-semibold text-[#64748B] hover:text-[#0F172A]"
								>
									Discard
								</button>
								<button
									on:click={saveEdit}
									class="btn btn-primary text-sm px-8"
								>
									Save Changes
								</button>
							</div>
						{:else}
							<div class="relative group min-h-[400px]">
								<button
									on:click={startEditing}
									class="absolute -top-6 -right-6 p-2.5 bg-white rounded-full shadow-lg border border-[#E2E8F0] text-[#64748B] hover:text-[#0369A1] opacity-0 group-hover:opacity-100 transition-all duration-200"
									title="Edit Letter Content"
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
											d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
										/>
									</svg>
								</button>
								{#each coverLetter.split("\n\n") as paragraph}
									<p
										class="text-[#0F172A] text-lg leading-relaxed mb-6 whitespace-pre-line last:mb-0"
									>
										{paragraph}
									</p>
								{/each}
							</div>
						{/if}
					</div>
				</div>

				<!-- Header Edit Section -->
				<div class="mb-10">
					<details
						class="group border border-[#E2E8F0] rounded-lg overflow-hidden transition-all bg-white shadow-sm"
					>
						<summary
							class="flex justify-between items-center p-5 cursor-pointer hover:bg-[#F8FAFC] transition-colors focus:outline-none list-none"
						>
							<div class="flex items-center gap-3">
								<div
									class="p-2 rounded-md bg-[#F1F5F9] text-[#475569]"
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
											d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
										/>
									</svg>
								</div>
								<h3 class="text-base font-bold text-[#0F172A]">
									Edit PDF Header Information
								</h3>
							</div>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5 text-[#64748B] transition-transform duration-200 group-open:rotate-180"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 9l-7 7-7-7"
								/>
							</svg>
						</summary>
						<div
							class="p-8 border-t border-[#E2E8F0] space-y-8 bg-white"
						>
							<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
								<div>
									<label
										for="header-firstname"
										class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
										>First Name</label
									>
									<input
										id="header-firstname"
										type="text"
										bind:value={firstName}
										on:input={() => {
											invalidatePdf();
											updateNameInCoverLetter();
										}}
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
								<div>
									<label
										for="header-surname"
										class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
										>Family Name</label
									>
									<input
										id="header-surname"
										type="text"
										bind:value={surname}
										on:input={() => {
											invalidatePdf();
											updateNameInCoverLetter();
										}}
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
							</div>

							<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
								<div class="md:col-span-2">
									<label
										for="header-street"
										class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
										>Street Address</label
									>
									<input
										id="header-street"
										type="text"
										bind:value={addressStreet}
										on:input={invalidatePdf}
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
								<div>
									<label
										for="header-postcode"
										class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
										>Postcode</label
									>
									<input
										id="header-postcode"
										type="text"
										bind:value={addressPostcode}
										on:input={invalidatePdf}
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
								<div>
									<label
										for="header-city"
										class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
										>City & Country</label
									>
									<div class="flex gap-2">
										<input
											id="header-city"
											type="text"
											bind:value={addressCity}
											on:input={invalidatePdf}
											class="input flex-1"
											placeholder="City"
											disabled={isPdfGenerating}
										/>
										<input
											aria-label="Country"
											type="text"
											bind:value={addressCountry}
											on:input={invalidatePdf}
											class="input flex-1"
											placeholder="Country"
											disabled={isPdfGenerating}
										/>
									</div>
								</div>
							</div>

							<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
								<div>
									<label
										for="header-email"
										class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
										>Email Address</label
									>
									<input
										id="header-email"
										type="email"
										bind:value={email}
										on:input={invalidatePdf}
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
								<div>
									<label
										for="header-phone"
										class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
										>Phone Number</label
									>
									<input
										id="header-phone"
										type="tel"
										bind:value={phone}
										on:input={invalidatePdf}
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
								<div>
									<label
										for="header-linkedin"
										class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
										>LinkedIn URL</label
									>
									<input
										id="header-linkedin"
										type="text"
										bind:value={linkedin}
										on:input={invalidatePdf}
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
							</div>
						</div>
					</details>
				</div>

				<!-- Version Selector -->
				{#if allCoverLetters.length > 1}
					<div
						class="mb-10 p-6 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl relative overflow-hidden"
					>
						<div class="flex items-center justify-between mb-6">
							<div>
								<h3 class="text-sm font-bold text-[#0F172A]">
									AI Race Results
								</h3>
								<p class="text-xs text-[#64748B]">
									Multiple models competed to write this
									letter. View alternatives below.
								</p>
							</div>
							{#if isLoadingAlternatives}
								<div
									class="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-[#0369A1]"
								>
									<svg
										class="animate-spin h-3 w-3"
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
									Syncing...
								</div>
							{/if}
						</div>

						<div class="flex flex-wrap gap-3">
							{#each allCoverLetters as version, index}
								<button
									on:click={() => switchVersion(index)}
									disabled={version.status === "failed"}
									class="px-5 py-3 rounded-md text-sm font-semibold transition-all border flex items-center gap-2 shadow-sm {currentVersionIndex ===
									index
										? 'bg-[#0F172A] text-white border-[#0F172A] scale-105'
										: version.status === 'failed'
											? 'bg-red-50 text-red-500 border-red-100 cursor-not-allowed opacity-50'
											: 'bg-white text-[#475569] border-[#E2E8F0] hover:border-[#0369A1] hover:text-[#0369A1]'}"
								>
									{#if index === 0}
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-4 w-4 text-yellow-500"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-7.714 2.143L11 21l-2.286-6.857L1 12l7.714-2.143L11 3z"
											/>
										</svg>
									{/if}
									{version.source}
								</button>
							{/each}
						</div>
					</div>
				{:else}
					<div class="flex justify-between items-center mb-8 px-2">
						<div
							class="text-[10px] font-bold uppercase tracking-wider text-[#64748B]"
						>
							Generated by <span class="text-[#0369A1]"
								>{source || "AI Engine"}</span
							>
						</div>
						{#if isLoadingAlternatives}
							<div
								class="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-[#64748B] animate-pulse"
							>
								Generating alternatives...
							</div>
						{/if}
					</div>
				{/if}

				<div class="space-y-4 pt-4">
					{#if !pdfUrl}
						<button
							on:click={handleGeneratePdf}
							disabled={isPdfGenerating}
							class="btn btn-primary w-full py-5 text-lg flex items-center justify-center gap-3"
						>
							{#if isPdfGenerating}
								<svg
									class="animate-spin h-6 w-6 text-white"
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
								Preparing PDF...
							{:else}
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
										d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
									/>
								</svg>
								Download as PDF
							{/if}
						</button>
					{:else}
						<div
							class="bg-green-50 border border-green-100 rounded-xl p-8 text-center animate-in zoom-in-95 duration-500"
						>
							<div
								class="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm"
							>
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
										d="M5 13l4 4L19 7"
									/>
								</svg>
							</div>
							<h3 class="text-xl font-bold text-[#0F172A] mb-2">
								Ready for Submission
							</h3>
							<p
								class="text-[#334155] text-sm mb-6 max-w-xs mx-auto"
							>
								Your personalized cover letter has been
								generated and is ready for download.
							</p>

							<div class="flex flex-col gap-3">
								<button
									on:click={handleDownload}
									class="btn btn-primary w-full py-4 flex items-center justify-center gap-2"
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
											d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
										/>
									</svg>
									Download PDF
								</button>
								<button
									on:click={reset}
									class="text-[#64748B] hover:text-[#0F172A] text-sm font-semibold py-2"
								>
									Start Over
								</button>
							</div>
						</div>
					{/if}

					{#if !downloaded}
						<button
							on:click={reset}
							class="btn btn-secondary w-full py-4"
						>
							Start Over
						</button>
					{/if}
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
