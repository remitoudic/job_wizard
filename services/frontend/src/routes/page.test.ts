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
	getUserCVs: vi.fn().mockResolvedValue([]),
	API_URL: 'http://test'
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
			job_id: 'mock-job-id'
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
		render(Page, { props: { data: {} } } as any);

		// Progress to Step 2/3: type in URL and click Next
		const input = screen.getByPlaceholderText(/linkedin\.com\/jobs/i);
		await fireEvent.input(input, { target: { value: 'https://linkedin.com/jobs/123' } });

		const nextButton = screen.getByText('Next Step');
		await fireEvent.click(nextButton);
	});

	it('should have a correctly linked upload info file input', async () => {
		render(Page, { props: { data: {} } } as any);

		// Open the 'Personalize your letter' details section
		// There are two elements with this text; pick the first one
		const [personalizeSummary] = screen.getAllByText('Personalize your letter');
		await fireEvent.click(personalizeSummary);

		// testing-library uses the linked <label> text to find the input element.
		// If the `for` attribute and the `id` don't match, this will throw a TestingLibraryElementError
		const fileInput = screen.getByLabelText(/choose file/i);

		expect(fileInput).toBeInTheDocument();
		expect(fileInput.tagName).toBe('INPUT');
		expect(fileInput).toHaveAttribute('type', 'file');
	});
});
