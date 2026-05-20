#!/usr/bin/env bash
# =============================================================================
# run_unittest.sh — Run all unit tests in the Job Wizard project
#
# Runs tests directly on the host machine (no Docker required).
#
# Usage:
#   ./scripts/run_unittest.sh                          # Run all unit tests
#   ./scripts/run_unittest.sh backend                  # Run only backend tests
#   ./scripts/run_unittest.sh frontend                 # Run only frontend tests
#   ./scripts/run_unittest.sh database                 # Run only database tests
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# ─────────────────────────────────────────────────────────────────────────────
# Helper functions for status messages
# ─────────────────────────────────────────────────────────────────────────────
info()  { echo "  [INFO]  $*"; }
ok_msg()    { echo "  [OK]    $*"; }
warn()  { echo "  [WARN]  $*" >&2; }

# ─────────────────────────────────────────────────────────────────────────────
# Extract a number preceding a keyword from a log file.
# Example: if the log contains "67 passed", extract_number file.log "passed" → "67"
# ─────────────────────────────────────────────────────────────────────────────
extract_number() {
  local file="$1"
  local pattern="$2"
  grep -Eo "[0-9]+ ${pattern}" "$file" 2>/dev/null | tail -1 | grep -Eo "[0-9]+" || echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# Extract the code coverage percentage from pytest's --cov output.
# Looks for a line containing TOTAL and a percentage like "50%".
# ─────────────────────────────────────────────────────────────────────────────
extract_coverage() {
  local file="$1"
  grep "TOTAL" "$file" 2>/dev/null | tail -1 | grep -Eo "[0-9]+%" | tail -1 | grep -Eo "[0-9]+" || echo ""
}

# ── Global state ────────────────────────────────────────────────────────────
EXIT_CODE=0
TARGET=""

# ── Temp directory for per-suite results ────────────────────────────────────
RESULTS_DIR=$(mktemp -d)
trap 'rm -rf "$RESULTS_DIR"' EXIT

BACKEND_RESULT="$RESULTS_DIR/backend"
FRONTEND_RESULT="$RESULTS_DIR/frontend"
DATABASE_RESULT="$RESULTS_DIR/database"

# ─────────────────────────────────────────────────────────────────────────────
# Parse CLI arguments — picks the target service name.
# Example:  ./run_unittest.sh backend
# ─────────────────────────────────────────────────────────────────────────────
parse_args() {
  for arg in "$@"; do
    case "$arg" in
      *) TARGET="$arg" ;;
    esac
  done
}

# ─────────────────────────────────────────────────────────────────────────────
# Backend test runner (Python / pytest)
#
# Tests location: services/backend/tests/unit/
# Runner:        uv run pytest (or plain pytest if uv is not available)
# Coverage:      pytest --cov=app --cov-report=html
# Output:        services/backend/coverage_html/index.html
# ─────────────────────────────────────────────────────────────────────────────
run_backend() {
  echo ""
  echo "--- Backend Tests (pytest) ---"

  local backend_dir="$PROJECT_ROOT/services/backend"
  local cov_opts="--cov=app --cov-report=term --cov-report=html:coverage_html"

  if command -v uv &>/dev/null; then
    (cd "$backend_dir" && uv run pytest tests/unit/ -v $cov_opts "$@" 2>&1 | tee "$BACKEND_RESULT.log" | tail -30) || true
  elif command -v pytest &>/dev/null; then
    (cd "$backend_dir" && pytest tests/unit/ -v $cov_opts "$@" 2>&1 | tee "$BACKEND_RESULT.log" | tail -30) || true
  else
    warn "Neither 'uv' nor 'pytest' found. Run: cd services/backend && uv sync --extra dev"
    echo "SKIP:0:0:" > "$BACKEND_RESULT"
    EXIT_CODE=1
    return
  fi

  local passed failed skipped total coverage_pct
  passed=$(extract_number "$BACKEND_RESULT.log" "passed")
  failed=$(extract_number "$BACKEND_RESULT.log" "failed")
  skipped=$(extract_number "$BACKEND_RESULT.log" "skipped")
  total=$(( ${passed:-0} + ${failed:-0} + ${skipped:-0} ))
  coverage_pct=$(extract_coverage "$BACKEND_RESULT.log")

  if [ -z "${failed:-}" ] || [ "$failed" -eq 0 ]; then
    echo "PASS:${passed:-0}:${total:-0}:${coverage_pct:-}" > "$BACKEND_RESULT"
  else
    echo "FAIL:${passed:-0}:${total:-0}:${coverage_pct:-}" > "$BACKEND_RESULT"
    EXIT_CODE=1
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Frontend test runner (Svelte / vitest)
#
# Tests location: services/frontend/src/**/*.test.ts
# Runner:        bun run test (vitest under the hood)
# Config:        services/frontend/vitest.config.ts
# ─────────────────────────────────────────────────────────────────────────────
run_frontend() {
  echo ""
  echo "--- Frontend Tests (vitest) ---"

  local frontend_dir="$PROJECT_ROOT/services/frontend"

  if command -v bun &>/dev/null; then
    (cd "$frontend_dir" && bun run svelte-kit sync 2>/dev/null || true)
    (cd "$frontend_dir" && bun run test "$@" 2>&1 | tee "$FRONTEND_RESULT.log" | tail -15) || true
  elif command -v npx &>/dev/null && command -v node &>/dev/null; then
    (cd "$frontend_dir" && npx svelte-kit sync 2>/dev/null || true)
    (cd "$frontend_dir" && npx vitest run "$@" 2>&1 | tee "$FRONTEND_RESULT.log" | tail -15) || true
  else
    warn "Neither 'bun' nor 'npx' found. Install: curl -fsSL https://bun.sh/install | bash"
    echo "SKIP:0:0:" > "$FRONTEND_RESULT"
    EXIT_CODE=1
    return
  fi

  local test_files_passed tests_passed test_files_failed tests_failed
  test_files_passed=$(grep -Eo "[0-9]+ passed" "$FRONTEND_RESULT.log" 2>/dev/null | head -1 | grep -Eo "[0-9]+" || echo "0")
  tests_passed=$(grep -Eo "[0-9]+ passed" "$FRONTEND_RESULT.log" 2>/dev/null | tail -1 | grep -Eo "[0-9]+" || echo "0")
  test_files_failed=$(grep -Eo "[0-9]+ failed" "$FRONTEND_RESULT.log" 2>/dev/null | head -1 | grep -Eo "[0-9]+" || echo "0")
  tests_failed=$(grep -Eo "[0-9]+ failed" "$FRONTEND_RESULT.log" 2>/dev/null | tail -1 | grep -Eo "[0-9]+" || echo "0")

  if [ -z "${test_files_failed:-}" ] || [ "$test_files_failed" -eq 0 ]; then
    echo "PASS:${tests_passed}:${test_files_passed}:" > "$FRONTEND_RESULT"
  else
    echo "FAIL:${tests_passed}:${test_files_passed}:" > "$FRONTEND_RESULT"
    EXIT_CODE=1
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Database test runner (Python / pytest)
#
# Tests location: services/database/tests/
# Runner:        uv run pytest from the backend directory (db is a dependency)
# Coverage:      pytest --cov=database_pkg --cov-report=html
# Output:        services/database/coverage_html/index.html
# ─────────────────────────────────────────────────────────────────────────────
run_database() {
  echo ""
  echo "--- Database Tests (pytest) ---"

  local db_dir="$PROJECT_ROOT/services/database"
  local backend_dir="$PROJECT_ROOT/services/backend"
  local cov_opts="--cov=database_pkg --cov-report=term --cov-report=html:coverage_html"

  if command -v uv &>/dev/null; then
    (cd "$backend_dir" && uv run pytest "$db_dir/tests/" -v $cov_opts "$@" 2>&1 | tee "$DATABASE_RESULT.log" | tail -30) || true
  else
    warn "No 'uv' found. Run: cd services/backend && uv sync --extra dev"
    echo "SKIP:0:0:" > "$DATABASE_RESULT"
    EXIT_CODE=1
    return
  fi

  local passed failed total coverage_pct
  passed=$(extract_number "$DATABASE_RESULT.log" "passed")
  failed=$(extract_number "$DATABASE_RESULT.log" "failed")
  total=${passed:-0}
  coverage_pct=$(extract_coverage "$DATABASE_RESULT.log")

  if [ -z "${failed:-}" ] || [ "$failed" -eq 0 ]; then
    echo "PASS:${passed:-0}:${total:-0}:${coverage_pct:-}" > "$DATABASE_RESULT"
  else
    echo "FAIL:${passed:-0}:${total:-0}:${coverage_pct:-}" > "$DATABASE_RESULT"
    EXIT_CODE=1
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Print a summary table with pass/fail and coverage % for each tested service.
# ─────────────────────────────────────────────────────────────────────────────
print_summary() {
  echo ""
  echo "========================== Tests Report =========================="

  local grand_passed=0

  for service in backend frontend database; do
    local result_file="${RESULTS_DIR}/${service}"
    [ ! -f "$result_file" ] && continue

    IFS=':' read -r status count total coverage <<< "$(cat "$result_file")"

    case "$service" in
      backend)  name="Backend (Python / pytest)"  ;;
      frontend) name="Frontend (Svelte / vitest)" ;;
      database) name="Database (Python / pytest)" ;;
    esac

    local line="  ${name}  "

    if [ "$status" = "PASS" ]; then
      if [ "$service" = "frontend" ]; then
        line+="OK  ${count} test(s) in ${total} file(s)"
      else
        line+="OK  ${count} test(s)"
      fi
      grand_passed=$((grand_passed + count))
    elif [ "$status" = "FAIL" ]; then
      line+="FAILED  ${count} test(s) passed (some failed)"
    else
      line+="SKIPPED  (tools not found)"
    fi

    [ -n "$coverage" ] && line+="  |  Coverage: ${coverage}%"

    echo "$line"
  done

  echo ""
  if [ "$EXIT_CODE" -eq 0 ]; then
    echo "  Result: ${grand_passed} test(s) — all passed"
  else
    echo "  Result: some tests FAILED — review the output above"
  fi
  echo "================================================================"
}

# ═════════════════════════════════════════════════════════════════════════════
# Main entry point
# ═════════════════════════════════════════════════════════════════════════════

parse_args "$@"

if [ -z "$TARGET" ]; then
  TARGET="all"
fi

echo ""
echo "Job Wizard — Unit Test Runner"
echo ""

case "$TARGET" in
  all)
    run_backend
    run_frontend
    run_database
    ;;
  backend)
    run_backend
    ;;
  frontend)
    run_frontend
    ;;
  database)
    run_database
    ;;
  *)
    echo "Unknown target: $TARGET"
    echo "Usage: $0 [backend|frontend|database]"
    EXIT_CODE=1
    ;;
esac

print_summary

exit "$EXIT_CODE"
