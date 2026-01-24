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

### Local Development (Your Laptop)

```bash
git clone git@github.com:remitoudic/job_wizard.git
cd job_wizard
./scripts/start_locally.sh

# First time: pull the Ollama model
docker exec jobwizard-ollama ollama pull llama3.2:1b
```

**Access**: http://localhost:5173

### Production Server

```bash
# Safe update with auto-backup and rollback
./scripts/update-production.sh
```

📖 **Full Development Guide**: See [DEVELOPMENT.md](DEVELOPMENT.md) for complete instructions.

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
  - Tests the configured model (`google/gemma-3-27b-it:free`)
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


