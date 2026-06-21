import { auth } from '../stores/auth';
import { get } from 'svelte/store';

export const API_URL = import.meta.env.VITE_API_URL || '';

function getAuthHeaders(tokenOverride?: string) {
	const headers: Record<string, string> = {};
	const token = tokenOverride || get(auth).token;
	if (token) {
		headers['Authorization'] = `Bearer ${token}`;
	}
	return headers;
}

function getHeaders(tokenOverride?: string) {
	return {
		'Content-Type': 'application/json',
		...getAuthHeaders(tokenOverride)
	};
}

async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
	const fetchOptions: RequestInit = {
		...options,
		credentials: 'include'
	};
	return fetch(url, fetchOptions);
}

async function handleResponse<T = any>(response: Response, defaultError: string): Promise<T> {
	const text = await response.text();
	if (!response.ok) {
		let msg = defaultError;
		try {
			if (text) {
				const data = JSON.parse(text);
				if (data.detail) {
					msg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
				}
			}
		} catch {} // Ignore parse errors on error response
		throw new Error(msg);
	}
	if (!text) return {} as T;
	try {
		return JSON.parse(text);
	} catch {
		throw new Error('Invalid JSON response from server');
	}
}

export async function loginUser(formData: FormData) {
	const response = await apiFetch(`${API_URL}/api/auth/login`, {
		method: 'POST',
		body: formData
	});
	return handleResponse<any>(response, 'Login failed');
}

export async function registerUser(userData: any) {
	const response = await apiFetch(`${API_URL}/api/auth/register`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(userData)
	});
	return handleResponse<any>(response, 'Registration failed');
}

export async function getProfile() {
	const response = await apiFetch(`${API_URL}/api/users/me`, {
		method: 'GET',
		headers: getHeaders()
	});
	return handleResponse<any>(response, 'Failed to fetch profile');
}

export async function getHealth() {
	const response = await apiFetch(`${API_URL}/health`, {
		method: 'GET'
	});
	return handleResponse<any>(response, 'Health check failed');
}

export async function updateProfile(userData: any) {
	const response = await apiFetch(`${API_URL}/api/users/me`, {
		method: 'PATCH',
		headers: getHeaders(),
		body: JSON.stringify(userData)
	});
	return handleResponse<any>(response, 'Failed to update profile');
}

export interface JobDescription {
	title: string;
	company: string;
	description: string;
	requirements: string[];
	url: string;
	source?: string;
}

export interface CoverLetterRequest {
	job_description: JobDescription;
	user_name?: string;
	user_skills?: string;
	context_text?: string;
	custom_instructions?: string;
	language?: string; // "english" | "german"
}

export interface User {
	id: number;
	email: string;
	username?: string;
	first_name?: string;
	surname?: string;
	job_title?: string;
	linkedin_url?: string;
	portfolio_url?: string;
	website_url?: string;
	profile_picture_url?: string;
	preferred_language?: string;

	street?: string;
	city?: string;
	postcode?: string;
	country?: string;

	phone?: string;
	last_login?: string;
	is_superuser?: boolean;
}

export async function getUsers(token?: string): Promise<User[]> {
	const response = await apiFetch(`${API_URL}/api/users/`, {
		headers: getHeaders(token)
	});

	return handleResponse<User[]>(response, 'Failed to fetch users');
}

export interface CoverLetterResponse {
	cover_letter: string;
	job_title: string;
	company: string;
	first_name?: string;
	surname?: string;
	email?: string;
	phone?: string;
	linkedin?: string;
	website?: string;
	address?: string;
	address_street?: string;
	address_postcode?: string;
	address_city?: string;
	address_country?: string;
	user_name_detected?: string;
	source?: string;
	alternative_id?: string;
}

export interface UploadImageResponse {
	filename: string;
	url: string;
}

export async function uploadProfilePicture(file: Blob, token?: string): Promise<User> {
	const formData = new FormData();
	formData.append('file', file, 'profile.jpg');

	const response = await apiFetch(`${API_URL}/api/users/me/picture`, {
		method: 'POST',
		headers: getAuthHeaders(token),
		body: formData
	});

	return handleResponse<User>(response, 'Failed to upload profile picture');
}

export async function deleteProfilePicture(token?: string): Promise<User> {
	const response = await apiFetch(`${API_URL}/api/users/me/picture`, {
		method: 'DELETE',
		headers: getAuthHeaders(token)
	});

	return handleResponse<User>(response, 'Failed to delete profile picture');
}

export interface UploadContextResponse {
	filename: string;
	text: string;
}

export interface GeneratePdfRequest {
	cover_letter: string;
	job_title: string;
	company: string;
	user_name?: string;
	first_name?: string;
	surname?: string;
	image_filename?: string;
	email?: string;
	phone?: string;
	linkedin?: string;
	template_name?: string;
	custom_date?: string;
	custom_subject?: string;
	full_name?: string;
	address?: string;
	address_street?: string;
	address_postcode?: string;
	address_city?: string;
	address_country?: string;
}

export interface GeneratePdfResponse {
	filename: string;
	url: string;
}

export async function parseJobUrl(url: string): Promise<JobDescription> {
	const response = await apiFetch(`${API_URL}/api/parse-job`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ url })
	});

	return handleResponse<JobDescription>(response, 'Failed to parse job URL');
}

export async function generateCoverLetter(
	request: CoverLetterRequest
): Promise<{ job_id: string }> {
	const response = await apiFetch(`${API_URL}/api/generate-cover-letter`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(request)
	});

	return handleResponse<{ job_id: string }>(response, 'Failed to generate cover letter');
}

export async function uploadImage(file: File): Promise<UploadImageResponse> {
	const formData = new FormData();
	formData.append('file', file);

	const response = await apiFetch(`${API_URL}/api/upload-image`, {
		method: 'POST',
		body: formData
	});

	return handleResponse<UploadImageResponse>(response, 'Failed to upload image');
}

export async function uploadContext(file: File): Promise<UploadContextResponse> {
	const formData = new FormData();
	formData.append('file', file);

	const response = await apiFetch(`${API_URL}/api/upload-context`, {
		method: 'POST',
		body: formData
	});

	return handleResponse<UploadContextResponse>(response, 'Failed to upload context file');
}

export async function generatePdf(request: GeneratePdfRequest): Promise<GeneratePdfResponse> {
	const formData = new FormData();
	formData.append('cover_letter', request.cover_letter);
	formData.append('job_title', request.job_title);
	formData.append('company', request.company);
	if (request.user_name) {
		formData.append('user_name', request.user_name);
	}
	if (request.first_name) {
		formData.append('first_name', request.first_name);
	}
	if (request.surname) {
		formData.append('surname', request.surname);
	}
	if (request.image_filename) {
		formData.append('image_filename', request.image_filename);
	}
	if (request.email) formData.append('email', request.email);
	if (request.phone) formData.append('phone', request.phone);
	if (request.linkedin) formData.append('linkedin', request.linkedin);
	if (request.template_name) formData.append('template_name', request.template_name);
	if (request.custom_date) formData.append('custom_date', request.custom_date);
	if (request.custom_subject) formData.append('custom_subject', request.custom_subject);
	if (request.full_name) formData.append('full_name', request.full_name);
	if (request.address) formData.append('address', request.address);
	if (request.address_street) formData.append('address_street', request.address_street);
	if (request.address_postcode) formData.append('address_postcode', request.address_postcode);
	if (request.address_city) formData.append('address_city', request.address_city);
	if (request.address_country) formData.append('address_country', request.address_country);

	const headers: Record<string, string> = {};
	const token = get(auth).token;
	if (token) {
		headers['Authorization'] = `Bearer ${token}`;
	}

	const response = await apiFetch(`${API_URL}/api/generate-pdf`, {
		method: 'POST',
		headers: headers,
		body: formData
	});

	return handleResponse<GeneratePdfResponse>(response, 'Failed to generate PDF');
}

export async function getAlternativeCoverLetter(altId: string) {
	const response = await apiFetch(`${API_URL}/api/cover-letter/alternative/${altId}`);

	return handleResponse<any>(response, 'Alternative not ready or not found');
}

// Save Application Types
export interface GeneratedLetterData {
	model: string;
	letter: string;
	timestamp: string;
}

export interface SaveApplicationRequest {
	job_url: string;
	job_title: string;
	job_company: string;
	job_description: string;
	job_requirements: string[];
	job_source: string;
	generated_letters: GeneratedLetterData[];
	selected_letter_index: number;
	header: Record<string, any>;
	cover_letter_body: string;
}

export interface SaveApplicationResponse {
	success: boolean;
	application_id: number;
	job_description_id: number;
	generated_letter_id: number;
	message: string;
}

export interface ApplicationListItem {
	id: number;
	job_title: string;
	company: string;
	job_url: string;
	status: string;
	created_at: string;
	header?: Record<string, any>;
	cover_letter_final?: Record<string, any>;
	job_description?: string;
	requirements?: string[];
	detailsLoaded?: boolean;
}

export interface FetchApplicationsResponse {
	applications: ApplicationListItem[];
	total: number;
}

export async function saveApplication(
	request: SaveApplicationRequest
): Promise<SaveApplicationResponse> {
	const response = await apiFetch(`${API_URL}/api/save-application`, {
		method: 'POST',
		headers: getHeaders(),
		body: JSON.stringify(request)
	});

	return handleResponse<SaveApplicationResponse>(response, 'Failed to save application');
}

export async function fetchUserApplications(
	skip: number = 0,
	limit: number = 50,
	includeDetails: boolean = false,
	sortBy: string = 'created_at',
	sortOrder: string = 'desc',
	company: string = ''
): Promise<FetchApplicationsResponse> {
	let url = `${API_URL}/api/applications?skip=${skip}&limit=${limit}&include_details=${includeDetails}&sort_by=${sortBy}&sort_order=${sortOrder}`;

	if (company) {
		url += `&company=${encodeURIComponent(company)}`;
	}

	const response = await apiFetch(url, {
		method: 'GET',
		headers: getHeaders()
	});

	return handleResponse<FetchApplicationsResponse>(response, 'Failed to fetch applications');
}

export interface ApplicationDetails {
	id: number;
	job_title: string;
	company: string;
	status: string;
	job_url: string;
	header: Record<string, any>;
	cover_letter_final: Record<string, any>;
	notes?: string;
	job_description: string;
	requirements: string[];
}

export async function fetchApplicationDetails(id: number): Promise<ApplicationDetails> {
	const response = await apiFetch(`${API_URL}/api/application/${id}/details`, {
		method: 'GET',
		headers: getHeaders()
	});

	return handleResponse<ApplicationDetails>(response, 'Failed to fetch application details');
}

export async function fetchUserCompanies(): Promise<string[]> {
	const response = await apiFetch(`${API_URL}/api/applications/companies`, {
		method: 'GET',
		headers: getHeaders()
	});

	return handleResponse<string[]>(response, 'Failed to fetch companies');
}

export interface UpdateApplicationRequest {
	job_title?: string;
	company?: string;
	status?: string;
	notes?: string;
	header?: Record<string, any>;
	cover_letter_body?: string;
}

export async function updateApplication(id: number, data: UpdateApplicationRequest): Promise<any> {
	const response = await apiFetch(`${API_URL}/api/application/${id}`, {
		method: 'PATCH',
		headers: getHeaders(),
		body: JSON.stringify(data)
	});

	return handleResponse<any>(response, 'Failed to update application');
}

export interface CreateApplicationRequest {
	job_title: string;
	company: string;
	job_url?: string;
	status?: string;
	notes?: string;
	cover_letter_body?: string;
}

export async function createApplication(
	data: CreateApplicationRequest
): Promise<{ success: boolean; application_id: number }> {
	const response = await apiFetch(`${API_URL}/api/application`, {
		method: 'POST',
		headers: getHeaders(),
		body: JSON.stringify(data)
	});

	return handleResponse<{ success: boolean; application_id: number }>(
		response,
		'Failed to create application'
	);
}

export interface DuplicateCheckResponse {
	is_duplicate: boolean;
	existing_application: {
		id: number;
		job_title: string;
		company: string;
		status: string;
		notes: string | null;
		cover_letter_body: string;
		created_at: string;
	} | null;
}

export async function checkDuplicateApplication(jobUrl: string): Promise<DuplicateCheckResponse> {
	const response = await apiFetch(
		`${API_URL}/api/application/check-duplicate?job_url=${encodeURIComponent(jobUrl)}`,
		{
			method: 'GET',
			headers: getHeaders()
		}
	);

	return handleResponse<DuplicateCheckResponse>(response, 'Failed to check for duplicate');
}

export interface ApplicationStatusHistory {
	id: number;
	application_id: number;
	old_status: string | null;
	new_status: string;
	notes: string | null;
	created_at: string;
}

export async function fetchApplicationHistory(id: number): Promise<ApplicationStatusHistory[]> {
	const response = await apiFetch(`${API_URL}/api/application/${id}/history`, {
		method: 'GET',
		headers: getHeaders()
	});

	return handleResponse<ApplicationStatusHistory[]>(response, 'Failed to fetch status history');
}

export async function updateApplicationStatus(id: number, status: string): Promise<any> {
	const response = await apiFetch(`${API_URL}/api/application/${id}/status`, {
		method: 'PATCH',
		headers: getHeaders(),
		body: JSON.stringify({ status })
	});

	return handleResponse<any>(response, 'Failed to update status');
}

export async function deleteApplication(id: number): Promise<any> {
	const response = await apiFetch(`${API_URL}/api/application/${id}`, {
		method: 'DELETE',
		headers: getHeaders()
	});

	return handleResponse<any>(response, 'Failed to delete application');
}

export async function exportApplications(format: 'xlsx' | 'csv' = 'xlsx'): Promise<void> {
	const response = await apiFetch(`${API_URL}/api/applications/export?format=${format}`, {
		method: 'GET',
		headers: getAuthHeaders()
	});
	if (!response.ok) {
		const text = await response.text();
		let msg = 'Failed to export applications';
		try {
			const data = JSON.parse(text);
			if (data.detail) msg = data.detail;
		} catch {}
		throw new Error(msg);
	}
	const blob = await response.blob();
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	const today = new Date().toISOString().split('T')[0];
	a.href = url;
	a.download = `vite-a-job-applications-${today}.${format}`;
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	URL.revokeObjectURL(url);
}

// ── User CV Management Types & API ─────────────────────────────────────────

export interface UserCVRead {
	id: number;
	name: string;
	original_filename: string;
	cv_url: string;
	cv_data: string | null;
	is_active: boolean;
	user_id: number;
	created_at: string;
	updated_at: string;
}

export async function getUserCVs(): Promise<UserCVRead[]> {
	const response = await apiFetch(`${API_URL}/api/users/me/cvs/`, {
		method: 'GET',
		headers: getHeaders()
	});
	return handleResponse<UserCVRead[]>(response, 'Failed to fetch CVs');
}

export async function uploadUserCV(file: File, name: string): Promise<UserCVRead> {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('name', name);

	const token = get(auth).token;
	const response = await apiFetch(`${API_URL}/api/users/me/cvs/`, {
		method: 'POST',
		headers: token ? { Authorization: `Bearer ${token}` } : {},
		body: formData
	});
	return handleResponse<UserCVRead>(response, 'Failed to upload CV');
}

export async function updateUserCV(cvId: number, data: { name?: string }): Promise<UserCVRead> {
	const response = await apiFetch(`${API_URL}/api/users/me/cvs/${cvId}`, {
		method: 'PATCH',
		headers: getHeaders(),
		body: JSON.stringify(data)
	});
	return handleResponse<UserCVRead>(response, 'Failed to update CV');
}

export async function activateUserCV(cvId: number): Promise<UserCVRead> {
	const response = await apiFetch(`${API_URL}/api/users/me/cvs/${cvId}/activate`, {
		method: 'PATCH',
		headers: getHeaders()
	});
	return handleResponse<UserCVRead>(response, 'Failed to activate CV');
}

export async function deleteUserCV(cvId: number): Promise<void> {
	const response = await apiFetch(`${API_URL}/api/users/me/cvs/${cvId}`, {
		method: 'DELETE',
		headers: getHeaders()
	});
	await handleResponse<any>(response, 'Failed to delete CV');
}

export interface CVContact {
	name: string;
	email: string;
	phone: string;
	linkedin: string;
	address: string;
}

export interface CVExperience {
	title: string;
	company: string;
	start_date: string;
	end_date: string;
	description: string;
}

export interface CVEducation {
	degree: string;
	institution: string;
	start_date: string;
	end_date: string;
}

export interface CVData {
	contact: CVContact;
	summary: string;
	experiences: CVExperience[];
	education: CVEducation[];
	skills: string[];
	languages: string[];
}

export interface CVTemplate {
	name: string;
	label: string;
	description: string;
}

export async function uploadCV(file: File): Promise<CVData> {
	const formData = new FormData();
	formData.append('file', file);

	const response = await apiFetch(`${API_URL}/api/cv/upload`, {
		method: 'POST',
		headers: (() => {
			const h: Record<string, string> = {};
			const token = get(auth).token;
			if (token) h['Authorization'] = `Bearer ${token}`;
			return h;
		})(),
		body: formData
	});

	return handleResponse<CVData>(response, 'Failed to parse CV');
}

export async function getCVTemplates(): Promise<CVTemplate[]> {
	const response = await apiFetch(`${API_URL}/api/cv/templates`, {
		method: 'GET',
		headers: getHeaders()
	});

	return handleResponse<CVTemplate[]>(response, 'Failed to fetch CV templates');
}

export async function generateCV(data: CVData, template: string): Promise<Blob> {
	const response = await apiFetch(`${API_URL}/api/cv/generate`, {
		method: 'POST',
		headers: getHeaders(),
		body: JSON.stringify({ cv_data: data, template_name: template })
	});

	if (!response.ok) {
		const text = await response.text();
		let msg = 'Failed to generate CV';
		try {
			const d = JSON.parse(text);
			if (d.detail) msg = d.detail;
		} catch {}
		throw new Error(msg);
	}

	return response.blob();
}

export async function previewCV(data: CVData, template: string): Promise<string> {
	const response = await apiFetch(`${API_URL}/api/cv/preview`, {
		method: 'POST',
		headers: getHeaders(),
		body: JSON.stringify({ cv_data: data, template_name: template })
	});
	if (!response.ok) {
		throw new Error('Failed to load preview');
	}
	return response.text();
}

// ── API Keys Management ──────────────────────────────────────────────────

export interface ApiKeyRead {
	id: number;
	name: string;
	user_id: number;
	created_at: string;
	last_used_at: string | null;
}

export interface ApiKeyWithSecret extends ApiKeyRead {
	secret_key: string;
}

export async function getApiKeys(): Promise<ApiKeyRead[]> {
	const response = await apiFetch(`${API_URL}/api/keys`, {
		method: 'GET',
		headers: getHeaders()
	});
	return handleResponse<ApiKeyRead[]>(response, 'Failed to fetch API keys');
}

export async function createApiKey(name: string): Promise<ApiKeyWithSecret> {
	const response = await apiFetch(`${API_URL}/api/keys`, {
		method: 'POST',
		headers: getHeaders(),
		body: JSON.stringify({ name })
	});
	return handleResponse<ApiKeyWithSecret>(response, 'Failed to create API key');
}

export async function deleteApiKey(keyId: number): Promise<void> {
	const response = await apiFetch(`${API_URL}/api/keys/${keyId}`, {
		method: 'DELETE',
		headers: getHeaders()
	});
	await handleResponse<any>(response, 'Failed to revoke API key');
}
