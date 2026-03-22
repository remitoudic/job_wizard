import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// Mock SvelteKit stores/app environment
vi.mock('$app/environment', () => ({
	browser: true,
	dev: true,
	building: false,
	version: 'any',
}));
vi.mock('$app/navigation', () => ({
	goto: vi.fn(),
}));
