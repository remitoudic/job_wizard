import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Page from './+page.svelte';
import { auth } from '../stores/auth';
import { step } from '../stores/wizard';
import * as api from '$lib/api';

// Mock the API module to prevent real fetch calls
vi.mock('$lib/api', () => ({
    getAlternativeCoverLetter: vi.fn(),
    parseJobUrl: vi.fn(),
    generateCoverLetter: vi.fn(),
    generatePdf: vi.fn(),
    uploadContext: vi.fn(),
    uploadImage: vi.fn(),
    saveApplication: vi.fn(),
    API_URL: 'http://test',
}));

describe('Cover Letter +page.svelte', () => {
    beforeEach(() => {
        step.set(1);
    });

    it('should pre-fill contact info from the auth store when logged in', async () => {
        // Setup API mocks to allow progressing to Step 3
        vi.mocked(api.parseJobUrl).mockResolvedValue({
            title: 'Mock Title',
            company: 'Mock Company',
            description: 'Mock Desc',
            requirements: [],
            url: 'http://test'
        });
        vi.mocked(api.generateCoverLetter).mockResolvedValue({
            cover_letter: 'Mock Cover Letter Text',
            job_title: 'Mock Title',
            company: 'Mock Company'
            // no contact info returned from API, to ensure UI uses auth!
        });

        // Set user in auth store
        auth.login('fake-token', {
            email: 'janedoe@example.com',
            first_name: 'Jane',
            surname: 'Doe',
            street: '123 Test St',
            city: 'Testville',
            postcode: '12345',
            country: 'Testland',
            phone: '555-0101',
            linkedin_url: 'https://linkedin.com/in/janedoe'
        });

        // The page component uses $auth natively
        render(Page, { props: { data: {} } });
        
        // Progress to Step 2/3: type in URL and click Next
        const input = screen.getByPlaceholderText(/linkedin\.com\/jobs/i);
        await fireEvent.input(input, { target: { value: 'https://linkedin.com/jobs/123' } });
        
        const nextButton = screen.getByText('Next Step');
        await fireEvent.click(nextButton);

        // Wait for component to mount and progress to Step 3
        await waitFor(() => {
            expect(screen.getByText(/Mock Cover Letter Text/i)).toBeInTheDocument();
        });

        // Find the UI elements that display the pre-filled info
        expect(screen.getByText(/Jane Doe/i)).toBeInTheDocument();
        expect(screen.getByText(/janedoe@example\.com/i)).toBeInTheDocument();
        expect(screen.getByText(/555-0101/i)).toBeInTheDocument();
        expect(screen.getByText(/123 Test St[\s\S]*12345[\s\S]*Testville/i)).toBeInTheDocument();
    });

    it('should have a correctly linked upload info file input', async () => {
        render(Page, { props: { data: {} } });
        
        // Open the 'Personalize your letter' details section
        const personalizeSummary = screen.getByText('Personalize your letter');
        await fireEvent.click(personalizeSummary);

        // testing-library uses the linked <label> text to find the input element.
        // If the `for` attribute and the `id` don't match, this will throw a TestingLibraryElementError
        const fileInput = screen.getByLabelText(/choose file/i);
        
        expect(fileInput).toBeInTheDocument();
        expect(fileInput.tagName).toBe('INPUT');
        expect(fileInput).toHaveAttribute('type', 'file');
    });
});

