const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface JobDescription {
    title: string;
    company: string;
    description: string;
    requirements: string[];
    url: string;
}

export interface CoverLetterRequest {
    job_description: JobDescription;
    user_name?: string;
    user_skills?: string;
}

export interface CoverLetterResponse {
    cover_letter: string;
    job_title: string;
    company: string;
}

export interface UploadImageResponse {
    filename: string;
    url: string;
}

export interface GeneratePdfRequest {
    cover_letter: string;
    job_title: string;
    company: string;
    user_name?: string;
    image_filename?: string;
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
