import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// Mock SvelteKit stores/app environment
vi.mock('$app/environment', () => ({
	browser: true,
	dev: true,
	building: false,
	version: 'any'
}));
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

// Mock EventSource for SSE — use a class so `new EventSource()` works as a constructor
class MockEventSource {
	url: string;
	readyState = 0;
	onopen: ((event: Event) => void) | null = null;
	onmessage: ((event: MessageEvent) => void) | null = null;
	onerror: ((event: Event) => void) | null = null;
	addEventListener = vi.fn();
	removeEventListener = vi.fn();
	close = vi.fn();

	constructor(url: string) {
		this.url = url;
	}
}

global.EventSource = MockEventSource as any;

// Mock URL methods for jsdom
if (typeof window !== 'undefined') {
	window.URL.createObjectURL = vi.fn().mockReturnValue('blob:mock-url');
	window.URL.revokeObjectURL = vi.fn();
}
