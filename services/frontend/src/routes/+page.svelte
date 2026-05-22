<script lang="ts">
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { step } from '../stores/wizard';
	import {
		parseJobUrl,
		generateCoverLetter,
		uploadImage,
		generatePdf,
		uploadContext,
		getAlternativeCoverLetter,
		saveApplication,
		getUserCVs,
		API_URL
	} from '$lib/api';
	import { auth } from '../stores/auth';
	import SEO from '$lib/components/SEO.svelte';
	import ContextPreview from '$lib/components/ContextPreview.svelte';
	import { generateCoverLetterFilename } from '$lib/pdfUtils';

	// SvelteKit automatically passes these props - declare them to avoid warnings
	export let data: any = {};

	let jobUrl = '';
	let userName = '';
	let imageFile: File | null = null;
	let imagePreview = '';
	let uploadedImageFilename = '';
	let contextText = '';
	let contextFilename = '';
	let customInstructions = '';

	// Settings
	let showSettings = false;
	// Single unified format selector: drives both template (PDF format) and language (AI writing)
	let selectedFormat: string = 'british';
	$: templateName = selectedFormat; // maps 1-to-1 to backend template_name
	$: language =
		selectedFormat === 'french'
			? 'french'
			: selectedFormat === 'german'
				? 'german'
				: selectedFormat === 'spanish'
					? 'spanish'
					: 'english';

	function handleLanguageSelect(e: Event) {
		handleLanguageChange((e.target as HTMLSelectElement).value);
	}

	function handleLanguageChange(newLang: string) {
		if (newLang === 'french') selectedFormat = 'french';
		else if (newLang === 'german') selectedFormat = 'german';
		else if (newLang === 'spanish') selectedFormat = 'spanish';
		else selectedFormat = 'british';
	}

	// Auto-detect language from job URL
	$: if (jobUrl) {
		try {
			// Ensure it has a protocol for robust URL parsing
			const urlStr = jobUrl.startsWith('http') ? jobUrl : `https://${jobUrl}`;
			const urlObj = new URL(urlStr);
			const hostname = urlObj.hostname.toLowerCase();
			const search = urlObj.search.toLowerCase();

			if (
				hostname.endsWith('.de') ||
				search.includes('language=de') ||
				search.includes('lang=de') ||
				search.includes('hl=de')
			) {
				selectedFormat = 'german';
			} else if (
				hostname.endsWith('.fr') ||
				search.includes('language=fr') ||
				search.includes('lang=fr') ||
				search.includes('hl=fr')
			) {
				selectedFormat = 'french';
			} else {
				// Fallback to simple string matching
				const lowerUrl = jobUrl.toLowerCase();
				if (lowerUrl.includes('.de/') || lowerUrl.endsWith('.de') || lowerUrl.includes('.de?')) {
					selectedFormat = 'german';
				} else if (
					lowerUrl.includes('.fr/') ||
					lowerUrl.endsWith('.fr') ||
					lowerUrl.includes('.fr?')
				) {
					selectedFormat = 'french';
				}
			}
		} catch (e) {
			// Fallback if URL parsing fails
			const lowerUrl = jobUrl.toLowerCase();
			if (lowerUrl.includes('.de/') || lowerUrl.endsWith('.de') || lowerUrl.includes('.de?')) {
				selectedFormat = 'german';
			} else if (
				lowerUrl.includes('.fr/') ||
				lowerUrl.endsWith('.fr') ||
				lowerUrl.includes('.fr?')
			) {
				selectedFormat = 'french';
			}
		}
	}

	// Contact Info
	let email = '';
	let phone = '';
	let linkedin = '';
	let website = '';
	let address = '';
	let addressStreet = '';
	let addressPostcode = '';
	let addressCity = '';
	let addressCountry = '';
	let firstName = '';
	let surname = '';

	let jobData: any = null;
	let coverLetter = '';
	let originalCoverLetter = ''; // Store original to allow re-replacing name
	let pdfUrl = '';
	let downloaded = false;

	let isParsing = false;
	let isGenerating = false;
	let generationProgress: Array<{ status: string; message: string; timestamp: number }> = [];
	let isPdfGenerating = false;
	let error = '';

	// Manual Input
	let isManualInput = false;
	let manualTitle = '';
	let manualCompany = '';
	let manualDescription = '';

	// Race Mode
	let alternativeId = '';
	let source = '';

	// Edit Mode - Body
	let isEditing = false;
	let tempCoverLetter = '';

	// Edit Mode - Header
	let isEditingName = false;
	let isEditingDate = false;
	let isEditingSubject = false;

	let editableName = '';
	let editableDate = '';
	let editableSubject = '';
	let editableJobTitle = '';
	let editableCompany = '';

	let isDateManuallyEdited = false;
	let isSubjectManuallyEdited = false;
	let hasAutoFilled = false;

	// User CVs for context
	let userCVs: any[] = [];
	let activeCV: any = null;
	let isLoadingCVs = false;

	async function fetchUserCVs() {
		if (!$auth.isAuthenticated) return;
		try {
			isLoadingCVs = true;
			const cvs = await getUserCVs();
			userCVs = cvs;
			activeCV = cvs.find((cv) => cv.is_active) || null;

			// If we have an active CV, and contextText is currently empty,
			// use the CV data as the context for LLM
			if (activeCV && !contextText) {
				// Use the parsed JSON data or raw content
				contextText = activeCV.cv_data || '';
			}
		} catch (err) {
			console.error('Failed to fetch user CVs:', err);
		} finally {
			isLoadingCVs = false;
		}
	}

	// Fetch CVs when user loggs in
	$: if ($auth.isAuthenticated) {
		fetchUserCVs();
	}

	// Sync contextText when activeCV changes (if not manually overridden by a file upload)
	$: if (activeCV && !contextFilename && !imageFile) {
		contextText = activeCV.cv_data || '';
	}

	// Update defaults when format changes
	$: if (selectedFormat && (jobData || isManualInput)) {
		const currentTitle = editableJobTitle || (jobData ? jobData.title : manualTitle);
		const currentCompany = editableCompany || (jobData ? jobData.company : manualCompany);

		if (selectedFormat === 'german') {
			if (!isDateManuallyEdited) {
				const now = new Date();
				const deMonths = [
					'Januar',
					'Februar',
					'März',
					'April',
					'Mai',
					'Juni',
					'Juli',
					'August',
					'September',
					'Oktober',
					'November',
					'Dezember'
				];
				editableDate = `${now.getDate()}. ${deMonths[now.getMonth()]} ${now.getFullYear()}`;
			}
			if (!isSubjectManuallyEdited) {
				editableSubject = `Bewerbung als ${currentTitle}`;
			}
		} else if (selectedFormat === 'french') {
			if (!isDateManuallyEdited) {
				const now = new Date();
				const frMonths = [
					'janvier',
					'février',
					'mars',
					'avril',
					'mai',
					'juin',
					'juillet',
					'août',
					'septembre',
					'octobre',
					'novembre',
					'décembre'
				];
				const cityPrefix = addressCity ? `À ${addressCity}, le ` : 'Le ';
				editableDate = `${cityPrefix}${now.getDate()} ${
					frMonths[now.getMonth()]
				} ${now.getFullYear()}`;
			}
			if (!isSubjectManuallyEdited) {
				editableSubject = `Objet : Candidature au poste de ${currentTitle}`;
			}
		} else if (selectedFormat === 'spanish') {
			if (!isDateManuallyEdited) {
				const now = new Date();
				const esMonths = [
					'enero',
					'febrero',
					'marzo',
					'abril',
					'mayo',
					'junio',
					'julio',
					'agosto',
					'septiembre',
					'octubre',
					'noviembre',
					'diciembre'
				];
				const cityPart = addressCity || 'Madrid'; // Fallback to Madrid
				editableDate = `${cityPart}, ${now.getDate()} de ${
					esMonths[now.getMonth()]
				} de ${now.getFullYear()}`;
			}
			if (!isSubjectManuallyEdited) {
				editableSubject = `Asunto: Candidatura para el puesto de ${currentTitle}`;
			}
		} else {
			if (!isDateManuallyEdited) {
				editableDate = new Date().toLocaleDateString('en-GB', {
					year: 'numeric',
					month: 'long',
					day: 'numeric'
				});
			}
			if (!isSubjectManuallyEdited) {
				editableSubject = `Re: Application for ${currentTitle} at ${currentCompany}`;
			}
		}
	}

	// Multiple cover letter versions
	let allCoverLetters: Array<{
		text: string;
		rawText: string; // Store original with [Your Name]
		source: string;
		status?: string;
	}> = [];
	let currentVersionIndex = 0;
	let isLoadingAlternatives = false;
	let hasAutoSelectedNvidia = false;
	let hasAutoSelectedMistral = false;
	let hasAutoSelectedQwen = false;

	// Reactive: Auto-select Nvidia/Qwen if it's in the list
	$: {
		if (allCoverLetters.length > 0) {
			console.log(
				'[AutoSelect] Current sources:',
				allCoverLetters.map((l) => l.source)
			);

			// 1. Priority: Mistral or Qwen (always switch to it even if we already selected a generic Nvidia)
			const bestModelIdx = allCoverLetters.findIndex(
				(l) =>
					(l.source.toLowerCase().includes('mistral') || l.source.toLowerCase().includes('qwen')) &&
					l.status !== 'failed' &&
					!l.text.startsWith('Generation failed')
			);

			if (bestModelIdx !== -1 && !hasAutoSelectedMistral && !hasAutoSelectedQwen) {
				console.log(`[AutoSelect] Found Priority Model at index ${bestModelIdx}. Switching...`);
				switchVersion(bestModelIdx);
				hasAutoSelectedMistral = true;
				hasAutoSelectedQwen = true;
				hasAutoSelectedNvidia = true;
			}
			// 2. Secondary: Generic Nvidia
			else if (!hasAutoSelectedNvidia) {
				const nvidiaIdx = allCoverLetters.findIndex(
					(l) =>
						l.source.toLowerCase().includes('nvidia') &&
						l.status !== 'failed' &&
						!l.text.startsWith('Generation failed')
				);
				if (nvidiaIdx !== -1) {
					console.log(`[AutoSelect] Found Nvidia at index ${nvidiaIdx}. Switching...`);
					switchVersion(nvidiaIdx);
					hasAutoSelectedNvidia = true;
				}
			}
		}
	}

	// Function to replace [Your Name] placeholder with actual name
	function updateNameInCoverLetter() {
		// Use the raw text of the current version as source
		const currentVersion = allCoverLetters[currentVersionIndex];
		const sourceText = currentVersion ? currentVersion.rawText : originalCoverLetter || coverLetter;

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
					(newText.includes('Sincerely,') || newText.includes('Best regards,'))
				) {
					// Regex to find Sincerely, followed by newlines and then ANY text to the end or double newline
					// This assumes the signature is the last thing or separated
					newText = newText.replace(/(Sincerely,|Best regards,)\s+[\s\S]+?$/i, `$1\n\n${fullName}`);
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
			error = 'Please enter a job URL';
			return;
		}

		isParsing = true;
		error = '';
		isManualInput = false;

		try {
			jobData = await parseJobUrl(jobUrl);
			editableJobTitle = jobData?.title || '';
			editableCompany = jobData?.company || '';
			if (advance) {
				step.set(2);
				// Auto-start generation in background
				handleGenerateCoverLetter();
			}
		} catch (e: any) {
			error = e.message || 'Failed to parse job URL';
		} finally {
			isParsing = false;
		}
	}

	async function handleFileUpload(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];

		if (file) {
			error = '';

			// Check if image or PDF
			if (file.type.startsWith('image/')) {
				imageFile = file;
				imagePreview = URL.createObjectURL(file);
				contextFilename = ''; // Clear context if switching to image

				try {
					const result = await uploadImage(file);
					uploadedImageFilename = result.filename;
				} catch (e: any) {
					error = 'Failed to upload image';
				}
			} else if (file.type === 'application/pdf') {
				// Handle PDF context
				imageFile = null;
				imagePreview = '';
				uploadedImageFilename = '';

				try {
					const result = await uploadContext(file);
					contextText = result.text;
					contextFilename = result.filename;
				} catch (e: any) {
					error = 'Failed to upload and parse PDF context';
				}
			} else {
				error = 'Please upload an image or PDF file';
			}
		}
	}

	async function handleGenerateCoverLetter() {
		if (!jobData) return;

		isGenerating = true;
		error = '';
		generationProgress = [];
		allCoverLetters = [];
		currentVersionIndex = 0;
		hasAutoSelectedNvidia = false;
		hasAutoSelectedMistral = false;
		hasAutoSelectedQwen = false;

		try {
			const { job_id } = await generateCoverLetter({
				job_description: jobData,
				user_name: userName || 'Applicant',
				context_text: contextText,
				custom_instructions: customInstructions,
				language
			});

			if (!job_id) throw new Error('No job ID received from server');

			// Open SSE connection
			const eventSource = new EventSource(`${API_URL}/api/events/${job_id}`);

			eventSource.onmessage = (event) => {
				const data = JSON.parse(event.data);

				// Add to progression list
				generationProgress = [
					...generationProgress,
					{
						status: data.status,
						message: data.message,
						timestamp: Date.now()
					}
				];

				// Handle Step: Extraction Done
				if (data.status === 'extracted' && data.contact_info) {
					const info = data.contact_info;
					if (info.first_name) firstName = info.first_name;
					if (info.surname) surname = info.surname;
					if (info.email) email = info.email;
					if (info.phone) phone = info.phone;
					if (info.linkedin) linkedin = info.linkedin;
					if (info.website) website = info.website;
					if (info.address) address = info.address;
					if (info.address_street) addressStreet = info.address_street;
					if (info.address_postcode) addressPostcode = info.address_postcode;
					if (info.address_city) addressCity = info.address_city;
					if (info.address_country) addressCountry = info.address_country;

					if (info.name && !userName) {
						userName = info.name;
					}
				}

				// Handle Step: Partial (Primary Ready)
				if (data.status === 'partial') {
					const primaryVersion = {
						text: data.text,
						rawText: data.text,
						source: data.source
					};

					if (allCoverLetters.length === 0) {
						allCoverLetters = [primaryVersion];
					} else {
						allCoverLetters[0] = primaryVersion;
						allCoverLetters = [...allCoverLetters];
					}

					// Only update the active text if we are still on the primary version
					if (currentVersionIndex === 0) {
						coverLetter = data.text;
						originalCoverLetter = data.text;
						source = data.source;
						alternativeId = data.alternative_id;

						if (firstName || surname) {
							updateNameInCoverLetter();
						}

						step.set(3);
					}
				}

				// If backend provided pre-finished alternatives, add them now
				if (data.alternatives && Array.isArray(data.alternatives)) {
					data.alternatives.forEach((alt: any) => {
						if (!allCoverLetters.some((l) => l.source === alt.source)) {
							allCoverLetters = [
								...allCoverLetters,
								{
									text: alt.text,
									rawText: alt.text,
									source: alt.source,
									status: alt.status || 'completed'
								}
							];
						}
					});
				}

				// Handle Step: Alternative Ready
				if (data.status === 'alternative_ready') {
					if (data.text && data.source && !allCoverLetters.some((l) => l.source === data.source)) {
						allCoverLetters = [
							...allCoverLetters,
							{
								text: data.text,
								rawText: data.text,
								source: data.source,
								status: 'completed'
							}
						];
					}

					// Always sync from data.alternatives if backend provides it
					if (data.alternatives && Array.isArray(data.alternatives)) {
						data.alternatives.forEach((alt: any) => {
							if (!allCoverLetters.some((l) => l.source === alt.source)) {
								allCoverLetters = [
									...allCoverLetters,
									{
										text: alt.text,
										rawText: alt.text,
										source: alt.source,
										status: alt.status || 'completed'
									}
								];
							}
						});
					}
				}

				// Handle Step: Completed
				if (data.status === 'completed') {
					// Update final result if we don't have it yet (e.g. race was instant)
					if (data.text && currentVersionIndex === 0) {
						const isUpdateNeeded = !coverLetter || source !== data.source;

						if (allCoverLetters.length === 0) {
							allCoverLetters = [
								{
									text: data.text,
									rawText: data.text,
									source: data.source
								}
							];
						} else {
							allCoverLetters[0] = {
								text: data.text,
								rawText: data.text,
								source: data.source
							};
							allCoverLetters = [...allCoverLetters];
						}

						if (
							isUpdateNeeded &&
							!hasAutoSelectedNvidia &&
							!hasAutoSelectedMistral &&
							!hasAutoSelectedQwen
						) {
							coverLetter = data.text;
							originalCoverLetter = data.text;
							source = data.source;
							alternativeId = data.alternative_id;
							step.set(3);
						}
					}

					// If backend provided pre-finished alternatives, add them now
					if (data.alternatives && Array.isArray(data.alternatives)) {
						data.alternatives.forEach((alt: any) => {
							if (!allCoverLetters.some((l) => l.source === alt.source)) {
								allCoverLetters = [
									...allCoverLetters,
									{
										text: alt.text,
										rawText: alt.text,
										source: alt.source,
										status: alt.status || 'completed'
									}
								];
							}
						});
					}

					isGenerating = false;
					eventSource.close();
				}

				// Handle Error
				if (data.status === 'error') {
					error = data.message;
					isGenerating = false;
					eventSource.close();
				}
			};

			eventSource.onerror = (e) => {
				console.error('SSE Connection Error', e);
				// We don't necessarily want to show error to user immediately
				// as SSE auto-reconnects, but if we are still generating and it fails...
			};

			// Initialize Editable Header Fields if not already edited
			if (!editableJobTitle) editableJobTitle = jobData?.title || '';
			if (!editableCompany) editableCompany = jobData?.company || '';
			editableName = firstName || surname ? `${firstName} ${surname}`.trim() : userName || '';
		} catch (e: any) {
			error = e.message || 'Failed to start generation';
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
				if (altResult.alternatives && Array.isArray(altResult.alternatives)) {
					newAlternatives = altResult.alternatives;
					isComplete = altResult.status === 'completed';
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
							status: alt.status || 'completed'
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

				// Check for Nvidia auto-selection during alternative polling
				if (!hasAutoSelectedNvidia) {
					const nvidiaIndex = allCoverLetters.findIndex(
						(l) =>
							(l.source.toLowerCase().includes('nvidia') ||
								l.source.toLowerCase().includes('mistral') ||
								l.source.toLowerCase().includes('qwen')) &&
							l.status !== 'failed' &&
							!l.text.startsWith('Generation failed')
					);
					if (nvidiaIndex !== -1) {
						console.log(
							`Auto-selected priority model from polled alternatives at index ${nvidiaIndex}`
						);
						switchVersion(nvidiaIndex);
						hasAutoSelectedNvidia = true;
						hasAutoSelectedMistral = true;
						hasAutoSelectedQwen = true;
					}
				}

				if (!isComplete) {
					// Poll again
					setTimeout(() => loadAlternatives(), 2000);
				} else {
					isLoadingAlternatives = false;
				}
			}
		} catch (e) {
			console.log('Error loading alternatives or not ready:', e);
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
			error = 'Please fill in all manual fields';
			return;
		}
		error = '';
		jobData = {
			title: manualTitle,
			company: manualCompany,
			description: manualDescription,
			requirements: [],
			url: jobUrl || `manual-${Date.now()}`
		};
		editableJobTitle = manualTitle;
		editableCompany = manualCompany;
		step.set(2);
	}

	async function handleGeneratePdf() {
		if (!coverLetter || !jobData) return;

		isPdfGenerating = true;
		error = '';

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
				address_country: addressCountry
			};

			// Saving application to database
			// Saving application to database (only if logged in)
			if ($auth.isAuthenticated) {
				try {
					await saveApplication({
						job_url: jobData.url || jobUrl || `manual-${Date.now()}`,
						job_title: editableJobTitle || jobData.title,
						job_company: editableCompany || jobData.company,
						job_description: jobData.full_description || jobData.description, // Use full description if available
						job_requirements: jobData.requirements,
						job_source: jobData.source || 'unknown',
						generated_letters: allCoverLetters.map((l) => ({
							model: l.source.includes('GPT') ? 'gpt-4o' : 'llama-3.2-1b', // precise mapping if possible, else approximation
							letter: l.text,
							timestamp: new Date().toISOString() // API expects this
						})),
						selected_letter_index: currentVersionIndex,
						header: header,
						cover_letter_body: coverLetter
					});
				} catch (err) {
					console.warn('Failed to save application to history:', err);
					// Continue to PDF generation even if save fails
				}
			}

			const result = await generatePdf({
				cover_letter: coverLetter,
				job_title: editableJobTitle || jobData.title,
				company: editableCompany || jobData.company,
				user_name: userName || 'Applicant',
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
				address_country: addressCountry
			});

			pdfUrl = result.url;

			// Auto-download
			handleDownload();
		} catch (e: any) {
			error = e.message || 'Failed to generate PDF';
		} finally {
			isPdfGenerating = false;
		}
	}

	async function handleDownload() {
		if (!pdfUrl) return;

		// The backend now returns a URL like /api/download/{filename}
		// or /api/uploads/{filename}. We need to prepend API_URL if not already there.
		const fullUrl = pdfUrl.startsWith('http') ? pdfUrl : `${API_URL}${pdfUrl}`;

		try {
			// Prepare headers
			const headers: Record<string, string> = {};
			if ($auth.token) {
				headers['Authorization'] = `Bearer ${$auth.token}`;
			}

			// Fetch blob with credentials to include cookies if token is null
			const response = await fetch(fullUrl, {
				headers,
				credentials: 'include'
			});

			if (!response.ok) {
				throw new Error(`Server returned ${response.status}: ${response.statusText}`);
			}

			const blob = await response.blob();
			const blobUrl = window.URL.createObjectURL(blob);

			const link = document.createElement('a');
			link.href = blobUrl;
			const company = jobData.company ? jobData.company.replace(/[^a-zA-Z0-9]/g, '_') : 'Company';
			const name =
				firstName || surname
					? `${firstName}_${surname}`.replace(/[^a-zA-Z0-9_]/g, '_')
					: (userName || 'Applicant').replace(/[^a-zA-Z0-9_]/g, '_');
			const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD

			link.download = generateCoverLetterFilename(language, name, company, date);
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
			console.error('Download failed:', e);
			// Fallback to direct link if fetch fails
			window.open(fullUrl, '_blank');
		}
	}

	function invalidatePdf() {
		if (pdfUrl) {
			pdfUrl = '';
			downloaded = false;
		}
	}

	function reset() {
		jobUrl = '';
		userName = '';
		imageFile = null;
		imagePreview = '';
		uploadedImageFilename = '';
		contextText = '';
		contextFilename = '';
		customInstructions = '';
		firstName = '';
		surname = '';
		email = '';
		phone = '';
		linkedin = '';
		jobData = null;
		coverLetter = '';
		pdfUrl = '';
		downloaded = false;
		hasAutoSelectedNvidia = false;
		isParsing = false;
		isGenerating = false;
		isPdfGenerating = false;
		error = '';
		step.set(1);

		// Reset format selection
		selectedFormat = 'british';
		isManualInput = false;
		manualTitle = '';
		manualCompany = '';
		manualDescription = '';

		// Reset Edit Modes
		isEditing = false;
		isEditingName = false;
		isEditingDate = false;
		isEditingSubject = false;
		editableName = '';
		editableDate = '';
		editableSubject = '';
		editableJobTitle = '';
		editableCompany = '';
		isDateManuallyEdited = false;
		isSubjectManuallyEdited = false;
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
		tempCoverLetter = '';
	}

	function toggleSettings() {
		showSettings = !showSettings;
	}

	// Pre-fill contact fields from logged-in user profile once available
	$: if ($auth.user && !hasAutoFilled) {
		const user = $auth.user;
		if (user.first_name) firstName = user.first_name;
		if (user.surname) surname = user.surname;
		if (user.email) email = user.email;
		if (user.phone) phone = user.phone;
		if (user.linkedin_url) linkedin = user.linkedin_url;
		if (user.website_url) website = user.website_url;
		if (user.street) addressStreet = user.street;
		if (user.postcode) addressPostcode = user.postcode;
		if (user.city) addressCity = user.city;
		if (user.country) addressCountry = user.country;

		const fullName = `${user.first_name || ''} ${user.surname || ''}`.trim();
		if (fullName) {
			userName = fullName;
			editableName = fullName;
		}
		hasAutoFilled = true;
	}

	// Close settings when clicking outside
	onMount(() => {
		const handleClickOutside = (event: MouseEvent) => {
			const settingsMenu = document.getElementById('settings-menu');
			const settingsBtn = document.getElementById('settings-btn');
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
		document.addEventListener('click', handleClickOutside);
		return () => document.removeEventListener('click', handleClickOutside);
	});
</script>

<SEO
	title="Vite a Job - AI Cover Letter Generator"
	description="Learn how to write a cover letter that beats the ATS. Our AI-powered generator creates professional, personalized applications in seconds to help you get more interviews."
/>

<div class="min-h-screen py-16 px-4">
	<div class="max-w-3xl mx-auto">
		<div class="text-center mb-16 px-4">
			<h1 class="text-5xl font-extrabold text-[#0F172A] tracking-tight mb-4">Vite a Job</h1>
			<p class="text-lg text-[#334155] max-w-lg mx-auto leading-relaxed">
				Craft professional, personalized cover letters in seconds. Just paste a LinkedIn job URL and
				let AI do the heavy lifting.
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
						class="mt-2 text-xs font-semibold uppercase tracking-wider {$step >= 1
							? 'text-[#0369A1]'
							: 'text-[#64748B]'}">Details</span
					>
				</div>
				<div class="w-20 h-0.5 {$step >= 2 ? 'bg-[#0369A1]' : 'bg-[#E2E8F0]'} -mt-6"></div>
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
						class="mt-2 text-xs font-semibold uppercase tracking-wider {$step >= 2
							? 'text-[#0369A1]'
							: 'text-[#64748B]'}">Review</span
					>
				</div>
				<div class="w-20 h-0.5 {$step >= 3 ? 'bg-[#0369A1]' : 'bg-[#E2E8F0]'} -mt-6"></div>
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
						class="mt-2 text-xs font-semibold uppercase tracking-wider {$step >= 3
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
								error = '';
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

		<!-- Step 1: Input -->
		{#if $step === 1}
			<div class="card">
				<div class="mb-8">
					<h2 class="text-2xl font-bold text-[#0F172A] mb-2">Get Started</h2>
					<div class="flex items-center justify-between">
						<p class="text-[#334155] text-sm">
							{#if isManualInput}
								Enter the job details manually below.
							{:else}
								Paste the link to the job posting below.
							{/if}
						</p>
						{#if !isManualInput}
							<button
								id="manual-entry-shortcut"
								on:click={() => {
									isManualInput = true;
									error = '';
								}}
								class="text-[#94A3B8] hover:text-[#0369A1] text-xs flex items-center gap-1 transition-colors duration-200"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-3 w-3"
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
								Enter manually
							</button>
						{:else}
							<button
								id="url-entry-shortcut"
								on:click={() => {
									isManualInput = false;
									error = '';
								}}
								class="text-[#94A3B8] hover:text-[#0369A1] text-xs flex items-center gap-1 transition-colors duration-200"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-3 w-3"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
									/>
								</svg>
								Use job URL
							</button>
						{/if}
					</div>
				</div>

				<div class="space-y-8">
					{#if isManualInput}
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
					{:else}
						<div class="relative">
							<input
								type="url"
								bind:value={jobUrl}
								placeholder="e.g. https://www.linkedin.com/jobs/view/..."
								class="input pr-12"
								disabled={isParsing}
							/>
							{#if isParsing}
								<div class="absolute right-4 top-1/2 -translate-y-1/2">
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

							{#if jobData && !isManualInput}
								<div
									class="mt-4 p-4 rounded-md border border-[#E2E8F0] bg-[#F8FAFC] flex items-center justify-between"
								>
									<div>
										<div class="text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-1">
											Parsed Position
										</div>
										<div class="font-semibold text-[#0F172A]">{jobData.title}</div>
										<div class="text-sm text-[#334155]">{jobData.company}</div>
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
					{/if}

					<div class="pt-2 border-t border-[#E2E8F0]">
						<details class="group">
							<summary
								class="flex justify-between items-center py-4 cursor-pointer text-[#334155] hover:text-[#0F172A] transition-colors focus:outline-none"
							>
								<div class="flex items-center gap-3">
									<span class="text-sm font-semibold">Personalize your letter</span>
								</div>

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
							<div class="pb-6 space-y-6 animate-in fade-in slide-in-from-top-2">
								<!-- Source of Truth (LLM Context) -->
								<ContextPreview
									activeCVName={activeCV ? activeCV.name : null}
									contextSnippet={contextText}
									isAuthenticated={$auth.isAuthenticated}
								/>

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
										value={language}
										on:change={handleLanguageSelect}
										class="w-full px-4 py-3 rounded-lg border border-[#E2E8F0] bg-white text-[#0F172A] focus:border-[#0369A1] focus:ring-2 focus:ring-[#0369A1]/20 outline-none transition-all text-sm mb-6"
									>
										<option value="english">English</option>
										<option value="german">German</option>
										<option value="french">French</option>
										<option value="spanish">Spanish</option>
									</select>
								</div>

								<div>
									<label
										for="custom-instructions"
										class="block text-sm font-semibold text-[#334155] mb-2">Custom Guidance</label
									>
									<p class="text-xs text-[#64748B] mb-3">
										Add specific instructions for the AI (e.g., "Focus on my leadership
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
										class="block text-sm font-semibold text-[#334155] mb-2">Upload info</label
									>
									<p class="text-xs text-[#64748B] mb-3">
										Upload information about yourself so that we can personalize your cover letter
										(for example, your CV).
									</p>
									<div class="flex items-center gap-4">
										<input
											type="file"
											id="file-upload-section"
											accept="image/*,.pdf"
											on:change={handleFileUpload}
											class="hidden"
											disabled={isParsing || activeCV}
										/>
										<label
											for="file-upload-section"
											class="btn btn-secondary text-sm cursor-pointer flex items-center gap-2 {activeCV
												? 'opacity-50 cursor-not-allowed grayscale'
												: ''}"
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
											<span class="text-sm font-medium text-green-600 flex items-center gap-1">
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
												{imageFile ? 'Image' : 'PDF'} Selected
											</span>
										{/if}
									</div>

									{#if imagePreview}
										<div class="mt-4 inline-block p-1 border border-[#E2E8F0] rounded-lg">
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
							if (isManualInput) {
								handleManualSubmit();
							} else if (jobData) {
								step.set(2);
							} else {
								handleParseJob(true);
							}
						}}
						disabled={(!isManualInput && (isParsing || !jobUrl)) ||
							(isManualInput && (!manualTitle || !manualCompany || !manualDescription))}
						class="btn btn-primary w-full py-4 text-lg"
					>
						{isParsing ? 'Analyzing Position...' : 'Next Step'}
					</button>
				</div>
			</div>
		{/if}

		<!-- Step 2: Review & Generate -->
		{#if $step === 2 && jobData}
			<div class="card">
				<div class="mb-8">
					<h2 class="text-2xl font-bold text-[#0F172A] mb-2">Review Position</h2>
					<p class="text-[#334155] text-sm">Verify the details before generating your letter.</p>
				</div>

				<div class="space-y-6 mb-10">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
						<div
							class="p-4 rounded-md bg-white border border-[#E2E8F0] focus-within:border-[#0369A1] transition-colors"
						>
							<label
								for="edit-role"
								class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
							>
								Role
							</label>
							<input
								id="edit-role"
								type="text"
								bind:value={editableJobTitle}
								class="w-full bg-transparent border-none p-0 text-lg font-bold text-[#0F172A] focus:ring-0 outline-none"
								placeholder="Job Title"
							/>
						</div>
						<div
							class="p-4 rounded-md bg-white border border-[#E2E8F0] focus-within:border-[#0369A1] transition-colors"
						>
							<label
								for="edit-company"
								class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
							>
								Company
							</label>
							<input
								id="edit-company"
								type="text"
								bind:value={editableCompany}
								class="w-full bg-transparent border-none p-0 text-lg font-bold text-[#0F172A] focus:ring-0 outline-none"
								placeholder="Company Name"
							/>
						</div>
					</div>

					<details class="group border border-[#E2E8F0] rounded-md overflow-hidden transition-all">
						<summary
							class="flex justify-between items-center p-4 cursor-pointer bg-white hover:bg-[#F8FAFC] transition-colors focus:outline-none"
						>
							<span class="text-sm font-semibold text-[#334155]">Full Job Description</span>
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
								<span class="text-[10px] font-bold uppercase tracking-wider text-[#64748B]">
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
								<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
									{#each jobData.requirements as req}
										<div class="flex items-start gap-2 text-sm text-[#334155]">
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
						on:click={() => (coverLetter ? step.set(3) : handleGenerateCoverLetter())}
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

				{#if isGenerating && generationProgress.length > 0}
					<div
						class="mt-8 p-6 bg-[#F8FAFC] rounded-2xl border border-[#E2E8F0] shadow-sm"
						transition:fade={{ duration: 300 }}
					>
						<h3
							class="text-sm font-bold text-[#475569] uppercase tracking-wider mb-4 flex items-center gap-2"
						>
							<span class="relative flex h-2 w-2">
								<span
									class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"
								></span>
								<span class="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
							</span>
							AI Engine Progression
						</h3>
						<div class="space-y-3">
							{#each generationProgress as progressItem, i}
								<div
									class="flex items-start gap-3 text-sm text-[#334155]"
									transition:fade={{ duration: 200 }}
								>
									<div class="mt-1">
										{#if i === generationProgress.length - 1 && isGenerating}
											<div
												class="w-4 h-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"
											></div>
										{:else}
											<svg
												class="w-4 h-4 text-green-500"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="3"
													d="M5 13l4 4L19 7"
												/>
											</svg>
										{/if}
									</div>
									<span
										class={i === generationProgress.length - 1
											? 'font-medium text-[#0F172A]'
											: 'opacity-60'}
									>
										{progressItem.message}
									</span>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Step 3: Result -->
		{#if $step === 3 && coverLetter}
			<div class="card relative">
				<div class="flex justify-between items-end mb-8 border-b border-[#E2E8F0] pb-6">
					<div>
						<h2 class="text-2xl font-bold text-[#0F172A] mb-1">Your Cover Letter</h2>
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
								<h3 class="text-sm font-bold text-[#0F172A] mb-4">Letter Preferences</h3>

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
												on:click={() => {
													selectedFormat = 'british';
													invalidatePdf();
												}}
												class="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg border text-left transition-all {selectedFormat ===
												'british'
													? 'border-[#0369A1] bg-[#EFF6FF] text-[#0369A1]'
													: 'border-[#E2E8F0] bg-white text-[#334155] hover:bg-[#F8FAFC]'}"
											>
												<span class="text-xl leading-none select-none">🇬🇧</span>
												<div class="flex-1 min-w-0">
													<div class="text-sm font-semibold leading-tight">British English</div>
													<div class="text-[11px] text-[#64748B] mt-0.5">
														Standard business format
													</div>
												</div>
												{#if selectedFormat === 'british'}
													<svg
														xmlns="http://www.w3.org/2000/svg"
														class="h-4 w-4 text-[#0369A1] shrink-0"
														viewBox="0 0 20 20"
														fill="currentColor"
													>
														<path
															fill-rule="evenodd"
															d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
															clip-rule="evenodd"
														/>
													</svg>
												{/if}
											</button>
											<button
												id="format-german"
												type="button"
												on:click={() => {
													selectedFormat = 'german';
													invalidatePdf();
												}}
												class="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg border text-left transition-all {selectedFormat ===
												'german'
													? 'border-[#0369A1] bg-[#EFF6FF] text-[#0369A1]'
													: 'border-[#E2E8F0] bg-white text-[#334155] hover:bg-[#F8FAFC]'}"
											>
												<span class="text-xl leading-none select-none">🇩🇪</span>
												<div class="flex-1 min-w-0">
													<div class="text-sm font-semibold leading-tight">Deutsch</div>
													<div class="text-[11px] text-[#64748B] mt-0.5">
														DIN 5008 · Bewerbungsschreiben
													</div>
												</div>
												{#if selectedFormat === 'german'}
													<svg
														xmlns="http://www.w3.org/2000/svg"
														class="h-4 w-4 text-[#0369A1] shrink-0"
														viewBox="0 0 20 20"
														fill="currentColor"
													>
														<path
															fill-rule="evenodd"
															d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
															clip-rule="evenodd"
														/>
													</svg>
												{/if}
											</button>
											<button
												id="format-french"
												type="button"
												on:click={() => {
													selectedFormat = 'french';
													invalidatePdf();
												}}
												class="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg border text-left transition-all {selectedFormat ===
												'french'
													? 'border-[#0369A1] bg-[#EFF6FF] text-[#0369A1]'
													: 'border-[#E2E8F0] bg-white text-[#334155] hover:bg-[#F8FAFC]'}"
											>
												<span class="text-xl leading-none select-none">🇫🇷</span>
												<div class="flex-1 min-w-0">
													<div class="text-sm font-semibold leading-tight">Français</div>
													<div class="text-[11px] text-[#64748B] mt-0.5">
														Motivation · Format standard
													</div>
												</div>
												{#if selectedFormat === 'french'}
													<svg
														xmlns="http://www.w3.org/2000/svg"
														class="h-4 w-4 text-[#0369A1] shrink-0"
														viewBox="0 0 20 20"
														fill="currentColor"
													>
														<path
															fill-rule="evenodd"
															d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
															clip-rule="evenodd"
														/>
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
					<div class="absolute top-0 left-0 w-1 h-full bg-[#0369A1]/20"></div>
					<!-- Live Header Preview -->
					<div
						class="mb-8 {['german', 'french'].includes(selectedFormat)
							? 'font-sans'
							: 'font-serif'}"
					>
						<!-- Line 1: Name -->
						<div class="text-base font-bold text-gray-900 mb-0.5 relative group w-fit">
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
									{editableName || '[Your Name]'}
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
								<span class="text-gray-400 italic text-sm">[Address not set]</span>
							{/if}
						</div>

						<!-- Line 3: Contact Info -->
						<div class="text-base text-gray-900 mb-6 pb-6 border-b border-gray-100">
							{#if email}<span>{email}</span>{/if}
							{#if email && phone}<span> | </span>{/if}
							{#if phone}<span>{phone}</span>{/if}
							{#if !email && !phone}
								<span class="text-gray-400 italic text-sm">[Contact info not set]</span>
							{/if}
						</div>

						{#if selectedFormat === 'british'}
							<!-- British Layout: Date then Recipient -->
							<div class="text-gray-800 mb-6 relative group w-fit ml-auto">
								{#if isEditingDate}
									<div class="flex items-center space-x-2 justify-end">
										<input
											type="text"
											bind:value={editableDate}
											on:input={() => (isDateManuallyEdited = true)}
											class="input py-1 px-2 text-right w-48"
										/>
										<button
											on:click={() => {
												isEditingDate = false;
												invalidatePdf();
											}}
											class="p-1 text-green-600 hover:bg-green-50 rounded">✓</button
										>
										<button
											on:click={() => (isEditingDate = false)}
											class="p-1 text-red-500 hover:bg-red-50 rounded">✕</button
										>
									</div>
								{:else}
									<div class="pl-8">
										{editableDate || '[Date]'}
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

							<div class="mb-6">
								<div class="text-base font-bold text-gray-900 mb-0.5">
									{editableCompany || jobData?.company || '[Company]'}
								</div>
								<div class="text-base text-gray-900 italic">
									{editableJobTitle || jobData?.title || '[Role]'}
								</div>
							</div>
						{:else if selectedFormat === 'french'}
							<!-- French Layout: Recipient Right, then Date Right -->
							<div class="mb-6 flex flex-col items-end">
								<div class="text-base font-bold text-gray-900 mb-0.5">
									{editableCompany || jobData?.company || '[Company]'}
								</div>
								<div class="text-base text-gray-900 italic">
									{editableJobTitle || jobData?.title || '[Role]'}
								</div>
							</div>

							<div class="text-gray-800 mb-10 relative group w-fit ml-auto">
								{#if isEditingDate}
									<div class="flex items-center space-x-2 justify-end">
										<input
											type="text"
											bind:value={editableDate}
											on:input={() => (isDateManuallyEdited = true)}
											class="input py-1 px-2 text-right w-48"
										/>
										<button
											on:click={() => {
												isEditingDate = false;
												invalidatePdf();
											}}
											class="p-1 text-green-600 hover:bg-green-50 rounded">✓</button
										>
										<button
											on:click={() => (isEditingDate = false)}
											class="p-1 text-red-500 hover:bg-red-50 rounded">✕</button
										>
									</div>
								{:else}
									<div class="pl-8">
										{editableDate || '[Lieu et Date]'}
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
						{:else}
							<!-- German DIN 5008 Layout: Recipient then Date -->
							<div class="mb-6">
								<div class="text-base font-bold text-gray-900 mb-0.5">
									{editableCompany || jobData?.company || '[Company]'}
								</div>
								<div class="text-base text-gray-900 italic">
									{editableJobTitle || jobData?.title || '[Role]'}
								</div>
							</div>

							<div class="text-gray-800 mb-6 relative group w-fit ml-auto">
								{#if isEditingDate}
									<div class="flex items-center space-x-2 justify-end">
										<input
											type="text"
											bind:value={editableDate}
											on:input={() => (isDateManuallyEdited = true)}
											class="input py-1 px-2 text-right w-48"
										/>
										<button
											on:click={() => {
												isEditingDate = false;
												invalidatePdf();
											}}
											class="p-1 text-green-600 hover:bg-green-50 rounded">✓</button
										>
										<button
											on:click={() => (isEditingDate = false)}
											class="p-1 text-red-500 hover:bg-red-50 rounded">✕</button
										>
									</div>
								{:else}
									<div class="pl-8">
										{editableDate || '[Date]'}
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
						{/if}

						<div
							class="text-gray-800 mb-8 {['german', 'french'].includes(selectedFormat)
								? 'font-sans font-bold'
								: 'font-serif font-semibold'} relative group w-fit"
						>
							{#if isEditingSubject}
								<div class="flex items-center space-x-2">
									<input
										type="text"
										bind:value={editableSubject}
										on:input={() => (isSubjectManuallyEdited = true)}
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
										on:click={() => (isEditingSubject = false)}
										class="p-1 text-red-500 hover:bg-red-50 rounded"
									>
										✕
									</button>
								</div>
							{:else}
								<div class="pr-8">
									{editableSubject || '[Subject]'}
									<button
										on:click={() => (isEditingSubject = true)}
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
					<div
						class="prose max-w-none {selectedFormat === 'german'
							? 'font-sans'
							: 'font-serif'} relative"
					>
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
								<button on:click={saveEdit} class="btn btn-primary text-sm px-8">
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
								{#each coverLetter.split('\n\n') as paragraph}
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
								<div class="p-2 rounded-md bg-[#F1F5F9] text-[#475569]">
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
								<h3 class="text-base font-bold text-[#0F172A]">Edit PDF Header Information</h3>
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
						<div class="p-8 border-t border-[#E2E8F0] space-y-8 bg-white">
							<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
								<div>
									<label
										for="header-jobtitle"
										class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
										>Job Title</label
									>
									<input
										id="header-jobtitle"
										type="text"
										bind:value={editableJobTitle}
										on:input={() => {
											invalidatePdf();
										}}
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
								<div>
									<label
										for="header-company"
										class="block text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2"
										>Company Name</label
									>
									<input
										id="header-company"
										type="text"
										bind:value={editableCompany}
										on:input={() => {
											invalidatePdf();
										}}
										class="input"
										disabled={isPdfGenerating}
									/>
								</div>
							</div>

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
								<h3 class="text-sm font-bold text-[#0F172A]">AI Race Results</h3>
								<p class="text-xs text-[#64748B]">
									Multiple models competed to write this letter. View alternatives below.
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
									disabled={version.status === 'failed'}
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
						<div class="text-[10px] font-bold uppercase tracking-wider text-[#64748B]">
							Generated by <span class="text-[#0369A1]">{source || 'AI Engine'}</span>
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
							<h3 class="text-xl font-bold text-[#0F172A] mb-2">Ready for Submission</h3>
							<p class="text-[#334155] text-sm mb-6 max-w-xs mx-auto">
								Your personalized cover letter has been generated and is ready for download.
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
						<button on:click={reset} class="btn btn-secondary w-full py-4"> Start Over </button>
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
