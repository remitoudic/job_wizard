---
description: CI Fixing workflow. Simulates the CI environment locally to systematically debug and fix failing tests, then pushes to GitHub Actions.
---

# /fix-ci - Continuous Integration Debugging and Fixing

$ARGUMENTS

---

## Purpose

This command is used when tests are failing in the CI pipeline (e.g. GitHub Actions) but passing locally, or when you need to resolve infrastructure-related integration test failures. It simulates the CI environment constraints locally to debug and fix test suite failures, then commits and pushes the fixes.

---

## Sub-commands

```
/fix-ci                - Run the full CI debugging and fixing workflow
/fix-ci [test_file]    - Simulate CI environment specifically for a failing test file
```

---

## Behavior

### Debugging and Fixing Flow

When asked to fix the CI:

1. **Analyze the CI Pipeline Configuration**
   - Review `.github/workflows/ci.yml` or equivalent.
   - Note the available services (e.g., PostgreSQL, Redis) and their connection strings.
   - Identify missing services in CI (e.g., Temporal, Ollama, Groq, specific LLM APIs) that might be causing integration test failures.

2. **Simulate CI Environment Locally**
   - Run tests locally with the `CI=true` environment variable to mimic GitHub Actions.
   - Example: `CI=true DATABASE_URL=postgresql://... uv run pytest tests`
   - Filter logs to identify the exact failing tests (`grep -E "^FAILED|^ERROR"`).

3. **Implement Fixes**
   - **Mocking**: For external services not present in CI (like Temporal or external APIs), robustly mock the clients (e.g. `patch('get_temporal_client')`).
   - **Skipping**: For integration tests that strictly require local infrastructure that cannot be mocked or is unavailable in CI (like local Ollama containers), add `@pytest.mark.skipif(os.environ.get("CI") == "true", reason="Requires local infrastructure")`.
   - **Deduplication / Flake Fixing**: Fix any race conditions or duplicate events (e.g., in SSE streams or async queues).

4. **Verify Locally (Tests and Linting)**
   - Re-run the simulated CI test command (e.g., `CI=true pytest`) to ensure all tests pass and skipped tests are correctly omitted.
   - Run the linting and formatting checks locally exactly as CI runs them: `uvx pre-commit run --all-files`.
   - **Crucial Formatting Gotchas**:
     - *Version Mismatches*: Always use `pre-commit run --all-files` rather than standalone commands (like `ruff format .`) so you use the exact linter versions defined in `.pre-commit-config.yaml`. Otherwise, slight formatting differences between versions will cause the CI to fail.
     - *Prettier Crashes in Svelte*: If Prettier crashes on a Svelte file (e.g., `SyntaxError`), check for `<script type="application/ld+json">` tags. Svelte interpolations like `{JSON.stringify(schema)}` are invalid JS and will crash Prettier. Add `<!-- prettier-ignore -->` immediately above the script tag to fix this.
   - If `pre-commit` modifies any files (like `ruff-format` or `prettier`), ensure those formatting fixes are added to the staging area before committing.

5. **Commit and Push**
   - Commit the fixes with a descriptive message (e.g., `fix: resolve integration tests for CI`).
   - Push to the repository (`git push origin main` or the active branch) to trigger the actual GitHub Actions CI pipeline.
   - Instruct the user to check the GitHub Actions tab.

---

## Example

```
/fix-ci
/fix-ci tests/integration/test_sse_events.py
```

---

## Key Principles

- **Never assume local parity**: Local environments often have running services (like Docker containers for Ollama or Temporal) that are absent in CI.
- **Robust Mocking**: Patch the client or connection factory, not just the service method, to ensure isolation.
- **Graceful Skipping**: Use `skipif` rather than deleting tests that are valuable locally but cannot run in CI.
- **Verify before pushing**: Always run with `CI=true` locally before pushing to avoid polluting the git history with failed CI fix attempts.
