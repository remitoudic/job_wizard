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

1. **Analyze the CI Pipeline Configuration & Diagnostic Logs**
   - Get the current commit SHA: `git rev-parse HEAD`
   - Retrieve all check runs for the commit from the GitHub API:
     ```bash
     curl -s "https://api.github.com/repos/{owner}/{repo}/commits/{sha}/check-runs" -H "Accept: application/vnd.github+json"
     ```
   - Get the detailed step-by-step conclusions of the actions run using the Run ID:
     ```bash
     curl -s "https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs" -H "Accept: application/vnd.github+json"
     ```
   - Identify the exact step that failed. Note if it failed in 0 seconds (which indicates a CLI usage, permission, or environment startup error rather than test failures).
   - Review `.github/workflows/ci.yml` or equivalent.
   - Note the available services (e.g., PostgreSQL, Redis) and their connection strings.

2. **Simulate CI Environment Locally**
   - Run tests locally with the `CI=true` environment variable to mimic GitHub Actions.
   - Example: `CI=true DATABASE_URL=postgresql://... uv run pytest tests`
   - Filter logs to identify the exact failing tests (`grep -E "^FAILED|^ERROR"`).

3. **Implement Fixes**
   - **Isolated Environments over Global Installs**: Do not install packages globally in GitHub Actions (`--system`) as they often conflict with pre-installed runner packages during downgrades. Instead, explicitly initialize a virtual environment using `uv venv` and install packages inside it.
   - **Nested Project / Monorepo `uv` traps**: If the repository has nested directories containing their own `pyproject.toml` (e.g. `services/backend/`), running `uv run` inside them will cause `uv` to look for a nested `.venv`. If it's not found, `uv` will spawn a new empty virtual environment. Prevent this by:
     - Executing tools via their explicit path relative to the root virtual environment (e.g. `../../.venv/bin/pytest tests`).
     - Passing the `--project` flag to direct `uv` to the correct root workspace context.
   - **Mocking**: For external services not present in CI (like Temporal or external APIs), robustly mock the clients (e.g. `patch('get_temporal_client')`).
   - **Skipping**: For integration tests that strictly require local infrastructure that cannot be mocked or is unavailable in CI (like local Ollama containers), add `@pytest.mark.skipif(os.environ.get("CI") == "true", reason="Requires local infrastructure")`.
   - **Deduplication / Flake Fixing**: Fix any race conditions or duplicate events (e.g., in SSE streams or async queues).

4. **Verify Locally (Tests and Linting)**
   - Re-run the simulated CI test command to ensure all tests pass and skipped tests are correctly omitted.
   - Run the linting and formatting checks locally exactly as CI runs them: `uvx pre-commit run --all-files`.
   - **Crucial Formatting & Typing Gotchas**:
     - *Version Mismatches*: Always use `pre-commit run --all-files` rather than standalone commands (like `ruff format .`) so you use the exact linter versions defined in `.pre-commit-config.yaml`. Otherwise, slight formatting differences between versions will cause the CI to fail.
     - *Pre-commit File Modifications*: If `pre-commit` modifies any files (like `prettier` formatting Svelte files), it will fail with exit code 1. **In CI, this causes a failure.** You MUST commit the formatting changes that `pre-commit` applied locally before pushing.
     - *Prettier Crashes in Svelte*: If Prettier crashes on a Svelte file (e.g., `SyntaxError`), check for `<script type="application/ld+json">` tags. Svelte interpolations like `{JSON.stringify(schema)}` are invalid JS and will crash Prettier. Add `<!-- prettier-ignore -->` immediately above the script tag to fix this.
     - *Svelte-Check Type Errors*: Unused props or accessibility warnings won't necessarily fail CI, but **TypeScript type errors** (e.g., mismatching interfaces in `src/lib/api.ts` vs backend schemas) will cause `bun run check` to exit with code 1. Always run `bun run check` locally after modifying data structures or APIs.
   - Ensure all `pre-commit` formatting fixes are added to the staging area and committed.

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

- **Pinpoint Failures via GitHub API**: Never guess the failure. Always run `curl` to fetch the status of the check runs and detailed job steps directly from the GitHub API.
- **Isolated Virtual Environments**: Always prefer isolated virtual environments over `--system` python package installations on CI runners to avoid system-level permissions and dependency conflicts.
- **Be Mindful of Monorepos**: When navigating nested directory structures, always call the explicit virtual environment path to bypass automatic project-lookup traps.
- **Never assume local parity**: Local environments often have running services (like Docker containers for Ollama or Temporal) that are absent in CI.
- **Robust Mocking**: Patch the client or connection factory, not just the service method, to ensure isolation.
- **Graceful Skipping**: Use `skipif` rather than deleting tests that are valuable locally but cannot run in CI.
- **Verify before pushing**: Always run with `CI=true` locally before pushing to avoid polluting the git history with failed CI fix attempts.
