const API_URL = import.meta.env.VITE_API_URL || '';

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

export interface CoverLetterResponse {
    cover_letter: string;
    job_title: string;
    company: string;
    email?: string;
    phone?: string;
    linkedin?: string;
    website?: string;
    address?: string;
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
    image_filename?: string;
    email?: string;
    phone?: string;
    linkedin?: string;
    template_name?: string;
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

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to parse job URL');
    }

    return response.json();
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

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate cover letter');
    }

    return response.json();
}

export async function uploadImage(file: File): Promise<UploadImageResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/api/upload-image`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to upload image');
    }

    return response.json();
}

export async function uploadContext(file: File): Promise<UploadContextResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/api/upload-context`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to upload context file');
    }

    return response.json();
}

export async function generatePdf(request: GeneratePdfRequest): Promise<GeneratePdfResponse> {
    const formData = new FormData();
    formData.append('cover_letter', request.cover_letter);
    formData.append('job_title', request.job_title);
    formData.append('company', request.company);
    if (request.user_name) {
        formData.append('user_name', request.user_name);
    }
    if (request.image_filename) {
        formData.append('image_filename', request.image_filename);
    }
    if (request.email) formData.append('email', request.email);
    if (request.phone) formData.append('phone', request.phone);
    if (request.linkedin) formData.append('linkedin', request.linkedin);
    if (request.template_name) formData.append('template_name', request.template_name);

    const response = await fetch(`${API_URL}/api/generate-pdf`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate PDF');
    }

    return response.json();
}

export async function getAlternativeCoverLetter(altId: string) {
    const response = await fetch(`${API_URL}/api/cover-letter/alternative/${altId}`);

    if (!response.ok) {
        throw new Error('Alternative not ready or not found');
    }

    return await response.json();
}
