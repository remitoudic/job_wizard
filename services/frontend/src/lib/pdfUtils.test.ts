import { describe, it, expect } from 'vitest';
import { generateCoverLetterFilename } from './pdfUtils';

describe('generateCoverLetterFilename', () => {
	const name = 'John_Doe';
	const company = 'TechCorp';
	const date = '2026-04-14';

	it('should generate the correct filename for English by default', () => {
		const filename = generateCoverLetterFilename('english', name, company, date);
		expect(filename).toBe(`coverletter_John_Doe_TechCorp_2026-04-14.pdf`);
	});

	it('should generate the correct filename for French', () => {
		const filename = generateCoverLetterFilename('french', name, company, date);
		expect(filename).toBe(`lettre_de_motivation_John_Doe_TechCorp_2026-04-14.pdf`);
	});

	it('should generate the correct filename for German with double underscore', () => {
		const filename = generateCoverLetterFilename('german', name, company, date);
		expect(filename).toBe(`anschreiben__John_Doe_TechCorp_2026-04-14.pdf`);
	});

	it('should generate the correct filename for Spanish', () => {
		const filename = generateCoverLetterFilename('spanish', name, company, date);
		expect(filename).toBe(`carta_de_presentacion_John_Doe_TechCorp_2026-04-14.pdf`);
	});

	it('should fallback to the english template for unknown languages', () => {
		const filename = generateCoverLetterFilename('italian', name, company, date);
		expect(filename).toBe(`coverletter_John_Doe_TechCorp_2026-04-14.pdf`);
	});
});
