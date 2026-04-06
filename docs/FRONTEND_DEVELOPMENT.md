# Frontend Development Guide

This guide covers the development workflow for the Vite/SvelteKit frontend service of the Job Wizard application.

## Testing with Bun and Vitest

We use **Vitest** for unit testing the frontend. To take advantage of faster startup and execution speeds, tests can be run natively using **Bun**.

### Prerequisites

Ensure you are located in the frontend repository directory:

```bash
cd services/frontend
```

Ensure Bun is installed on your system. If not, install it using `curl -fsSL https://bun.sh/install | bash`.

### Running Tests

Use `bunx vitest` to run tests. Bun replaces standard Node execution to run tests much faster.

**1. Run all tests in watch mode (Default)**
Running vitest without any arguments continuously watches for changes and re-runs tests on the fly:
```bash
bunx vitest
```

**2. Run a specific test file**
Give it the path to the test file to isolate test execution:
```bash
bunx vitest run src/routes/page.test.ts
```

**3. Run a test case by name**
Useful when tracking down a specific bug:
```bash
bunx vitest run -t "should have a correctly linked upload info file input"
```

**4. Run tests once without watching (for CI/CD)**
```bash
bunx vitest run
```

### Writing Tests

Tests are placed alongside their components and end in `.test.ts`. They use `@testing-library/svelte` to query and interact with the UI, ensuring components match accessibility and HTML correctness standards.

Example structure:
```typescript
import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import MyComponent from './MyComponent.svelte';

describe('MyComponent', () => {
    it('should behave correctly', async () => {
        render(MyComponent);
        // ... assertions and events ...
    });
});
```
