import { auth } from '../stores/auth';
import { get } from 'svelte/store';

export const API_URL = import.meta.env.VITE_API_URL || '';

function getHeaders() {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };

    // Inject token if available
    const token = get(auth).token;
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

async function handleResponse<T = any>(response: Response, defaultError: string): Promise<T> {
    const text = await response.text();
    if (!response.ok) {
        let msg = defaultError;
        try {
            if (text) {
                const data = JSON.parse(text);
                if (data.detail) {
                    msg = typeof data.detail === 'string'
                        ? data.detail
                        : JSON.stringify(data.detail);
                }
            }
        } catch { } // Ignore parse errors on error response
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
    const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        body: formData,
    });
    return handleResponse<any>(response, 'Login failed');
}

export async function registerUser(userData: any) {
    const response = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
    });
    return handleResponse<any>(response, 'Registration failed');
}

export async function getProfile() {
    const response = await fetch(`${API_URL}/api/users/me`, {
        method: 'GET',
        headers: getHeaders(),
    });
    return handleResponse<any>(response, 'Failed to fetch profile');
}

export async function updateProfile(userData: any) {
    const response = await fetch(`${API_URL}/api/users/me`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(userData),
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

    street?: string;
    city?: string;
    postcode?: string;
    country?: string;

    phone?: string;
    last_login?: string;
    is_superuser?: boolean;
}

export async function getUsers(token: string): Promise<User[]> {
    const response = await fetch(`${API_URL}/api/users/`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
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
    const response = await fetch(`${API_URL}/api/parse-job`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
    });

    return handleResponse<JobDescription>(response, 'Failed to parse job URL');
}

export async function generateCoverLetter(
    request: CoverLetterRequest
): Promise<CoverLetterResponse> {
    const response = await fetch(`${API_URL}/api/generate-cover-letter`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    return handleResponse<CoverLetterResponse>(response, 'Failed to generate cover letter');
}

export async function uploadImage(file: File): Promise<UploadImageResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/api/upload-image`, {
        method: 'POST',
        body: formData,
    });

    return handleResponse<UploadImageResponse>(response, 'Failed to upload image');
}

export async function uploadContext(file: File): Promise<UploadContextResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/api/upload-context`, {
        method: 'POST',
        body: formData,
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

    const response = await fetch(`${API_URL}/api/generate-pdf`, {
        method: 'POST',
        headers: headers,
        body: formData,
    });

    return handleResponse<GeneratePdfResponse>(response, 'Failed to generate PDF');
}

export async function getAlternativeCoverLetter(altId: string) {
    const response = await fetch(`${API_URL}/api/cover-letter/alternative/${altId}`);

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
    header: Record<string, any>;
    cover_letter_final: Record<string, any>;
    job_description: string;
    requirements: string[];
}

export interface FetchApplicationsResponse {
    applications: ApplicationListItem[];
}

export async function saveApplication(
    request: SaveApplicationRequest
): Promise<SaveApplicationResponse> {
    const response = await fetch(`${API_URL}/api/save-application`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(request),
    });

    return handleResponse<SaveApplicationResponse>(response, 'Failed to save application');
}

export async function fetchUserApplications(): Promise<FetchApplicationsResponse> {
    const response = await fetch(`${API_URL}/api/applications`, {
        method: 'GET',
        headers: getHeaders(),
    });

    return handleResponse<FetchApplicationsResponse>(response, 'Failed to fetch applications');
}

export async function updateApplicationStatus(id: number, status: string): Promise<any> {
    const response = await fetch(`${API_URL}/api/application/${id}/status`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify({ status }),
    });

    return handleResponse<any>(response, 'Failed to update status');
}
