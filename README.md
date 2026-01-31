# Job Wizard 🧙‍♂️

A web application that generates personalized cover letters from job descriptions using AI. Simply paste a job URL, upload your CV as a PDF (or any other background documents) as context and get a professionally formatted PDF cover letter. The more the system knows about you, the more personalized the cover letter will be.

## Features

- 🔗 **Smart Job Parsing**: Extracts job details from URLs using customizable proxies (no browser required)
- 🚀 **Hybrid LLM Engine**: "Race Mode" runs local (Ollama) and remote (Groq/OpenRouter) models in parallel for maximum speed
- 📄 **PDF Export**: Professional PDF format with embedded photo
- 🎨 **Modern UI**: Beautiful, responsive SvelteKit interface
- 🐳 **Docker Ready**: Complete multi-service architecture

## Architecture

```
                                      ┌─────────────┐
                                 ┌───▶│   Ollama    │
┌─────────────┐      ┌───────────┴─┐  │   (Local)   │
│  SvelteKit  │─────▶│   FasAPI    │  └─────────────┘
│  Frontend   │      │   Backend   │  ┌─────────────┐
└─────────────┘      └───────────┬─┘─▶│    Groq     │
                           │     │    │  (Primary)  │
                           │     │    └─────────────┘
                           ▼     │    ┌─────────────┐
                    ┌────────────┴┐──▶│ OpenRouter  │
                    │ PostgreSQL  │   │ (Failover)  │
                    │  Database   │   └─────────────┘
                    └─────────────┘
```

## Tech Stack

- **Backend**: FastAPI + Python 3.11 + uv (dependency management)
- **Frontend**: SvelteKit + TailwindCSS
- **LLM Strategy**: Hybrid (Ollama + Groq + OpenRouter)
- **Scraping**: httpx + BeautifulSoup4 + Smart Proxy Rotation
- **Database**: PostgreSQL 16 + SQLModel
- **Orchestration**: Docker Compose
- **Analytics**: Microsoft Clarity

## Prerequisites

- Docker & Docker Compose
- Git

## Quick Start

### Local Development

```bash
git clone git@github.com:remitoudic/job_wizard.git
cd job_wizard

# Start services
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
2. Paste a job description URL (LinkedIn, Indeed, etc.) or paste text manually
3. Upload your CV/PDF for context
4. Click "Generate Cover Letter" (Watch the race between AI models!)
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

# Run locally
uv run uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
bun install

# Run dev server
bun run dev -- --host 0.0.0.0 --port 5173
```

## Environment Variables

See `.env.example` for all configuration options. Key variables include:

- `GROQ_API_KEY`: Primary remote LLM provider (Fastest)
- `OPENROUTER_API_KEY`: Backup remote LLM provider
- `PROXY_FILE_PATH`: Path to standard JSON proxy list (ip, port, un, pw)
- `LOGFIRE_TOKEN`: (Optional) For observability and structured logging

## Project Structure

```
job_wizard/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── job_parser.py    # httpx + proxy logic
│   │   │   ├── llm_service.py   # Hybrid race logic
│   │   │   └── ...
│   ├── database/                # SQLModel definitions & migrations
│   └── ...
├── frontend/
│   ├── src/lib/components/      # Svelte components
│   └── ...
└── scripts/                     # Deployment & Utility scripts
```

## Troubleshooting

- **Ollama model not found?** Run `docker exec jobwizard-ollama ollama pull llama3.2:1b`
- **Scraping failed?** Check `proxies.json` or ensure the target URL is accessible.
- **Race mode issues?** Ensure at least one remote API key is set in `.env`.

## License

MIT


