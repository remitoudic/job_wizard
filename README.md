# Job Wizard 🧙‍♂️

A web application that generates personalized cover letters from job descriptions using AI. Simply paste a job URL, upload your CV as a PDF (or any other background documents) as context and get a professionally formatted PDF cover letter. The more the system knows about you, the more personalized the cover letter will be.

## Features

- 🔗 **Job Description Parsing**: Automatically extracts job details from URLs
- 🤖 **AI-Powered Generation**: Uses Ollama LLM to create personalized cover letters
- 📄 **PDF Export**: Professional PDF format with embedded photo
- 🎨 **Modern UI**: Beautiful, responsive SvelteKit interface
- 🐳 **Docker Ready**: Complete multi-service architecture

## Architecture

```
                                          ┌─────────────┐
                                     ┌───▶│   Ollama    │
┌─────────────┐      ┌─────────────┐ │    │   (Local)   │
│  SvelteKit  │─────▶│   FastAPI   │─┤    └─────────────┘
│  Frontend   │      │   Backend   │ │    ┌─────────────┐
└─────────────┘      └─────────────┘ └───▶│ OpenRouter  │
                            │             │   (Remote)  │
                            ▼             └─────────────┘
                     ┌─────────────┐
                     │ PostgreSQL  │
                     │  Database   │
                     └─────────────┘
```

## Tech Stack

- **Backend**: FastAPI + Python 3.11 + uv (dependency management)
- **Frontend**: SvelteKit + TailwindCSS
- **LLM**: Ollama (llama3.2:1b)
- **Database**: PostgreSQL 16
- **Orchestration**: Docker Compose

## Prerequisites

- Docker & Docker Compose
- Git

## Quick Start

1. **Clone and setup**
   ```bash
   git clone <your-repo-url>
   cd job_wizard
   cp .env.example .env
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Pull the LLM model** (first time only)
   ```bash
   docker-compose exec ollama ollama pull llama3.2:1b
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Usage

1. Open http://localhost:5173 in your browser
2. Paste a job description URL (LinkedIn, Indeed, etc.)
3. Upload your CV/PDF for context (and optional photo)
4. Click "Generate Cover Letter"
5. Review the AI-generated content
6. Download your PDF

## Development

### Backend Development

```bash
cd backend

# Install dependencies with uv
uv sync

# Run tests
uv run pytest

# Install Playwright browsers (Required for job parsing)
uv run playwright install chromium

# Run locally (without Docker)
uv run uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies (using Bun in the container)
bun install

# Run dev server
bun run dev -- --host 0.0.0.0 --port 5173

# Build for production
bun run build
```

### Testing

The project includes tests for both local (Ollama) and remote (OpenRouter) LLM providers.

#### Prerequisites

- Docker containers must be running (`docker compose up -d`)
- For OpenRouter tests: Set `OPENROUTER_API_KEY` in your `.env` file

#### Running Tests

**Run all tests:**
```bash
docker exec jobwizard-backend pytest tests/ -v
```

**Run specific tests:**
```bash
# Test Ollama connectivity
docker exec jobwizard-backend pytest tests/test_ollama.py -v

# Test OpenRouter connectivity
docker exec jobwizard-backend pytest tests/test_openrouter.py -v

# Test both LLM providers
docker exec jobwizard-backend pytest tests/test_ollama.py tests/test_openrouter.py -v
```

**Run with detailed output (see model responses):**
```bash
docker exec jobwizard-backend pytest tests/test_ollama.py -v -s
```

#### What the Tests Verify

- **Ollama Test** (`test_ollama.py`):
  - Verifies connection to local Ollama service
  - Checks that the configured model (`llama3.2:1b`) is available
  - Tests text generation capability

- **OpenRouter Test** (`test_openrouter.py`):
  - Verifies connection to OpenRouter API
  - Tests the configured model (`xiaomi/mimo-v2-flash:free`)
  - Validates API key authentication
  - Note: Skipped if `OPENROUTER_API_KEY` is not set

#### Expected Output

```
tests/test_ollama.py::test_ollama_connection PASSED
tests/test_openrouter.py::test_openrouter_connection PASSED
======================== 2 passed in X.XXs ========================
```

## Project Structure

```
job_wizard/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── services/
│   │   │   ├── job_parser.py
│   │   │   ├── llm_service.py
│   │   │   └── pdf_service.py
│   │   └── main.py
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   │   └── +page.svelte
│   │   └── lib/
│   │       └── api.ts
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Environment Variables

See `.env.example` for all configuration options.

## Troubleshooting

**Ollama model not found?**
```bash
docker-compose exec ollama ollama pull llama3.2:1b
```

**Port conflicts?**
Edit `.env` to change default ports.

**Frontend can't connect to backend?**
Check CORS settings in `.env` and ensure `VITE_API_URL` is correct.

## License

MIT

Parser improvements and headless fallback
---------------------------------------

If you hit 403 Forbidden errors when parsing job pages (some job sites actively block programmatic requests), the backend parser now:

- Sends realistic browser-like headers and retries transient 403/429/5xx responses with exponential backoff ✅
- Attempts a headless-browser fallback using Playwright if the HTTP approach fails (optional) 🔁

To enable the fallback in your environment:

```bash
# From the backend folder
pip install -e .[browser]
# Then install browser binaries
playwright install
```

To run the tests locally:

```bash
cd backend
pip install -e .[dev]
pytest -q
```
