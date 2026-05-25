import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';
import { readable, writable } from 'svelte/store';

// Mock svelte-i18n to prevent intl-messageformat ESM resolution issues in jsdom
vi.mock('svelte-i18n', () => {
	const locale = writable('en');
	const _ = readable((key: string, opts?: { default?: string }) => {
		return opts?.default || key;
	});
	const isLoading = readable(false);
	return {
		locale,
		_: _,
		isLoading,
		init: vi.fn(),
		addMessages: vi.fn(),
		getLocaleFromNavigator: vi.fn()
	};
});

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
