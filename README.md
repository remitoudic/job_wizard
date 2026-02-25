# Vite a Job! 🧙‍♂️

A web application that generates personalized cover letters from job descriptions using AI, and revitalizes your old CVs into clean, beautiful PDFs. Simply paste a job URL and your background info to get a custom cover letter, or upload your old CV to automatically parse and render it into a modern or classic template.

## Features

- 📄 **CV Refresh**: Upload your old PDF CV. Our AI (LlamaParse + Groq) extracts your experience, education, and contact details so you can quickly generate a sleek new CV using our Modern or Classic templates.
- 🔗 **Smart Job Parsing**: Extracts job details from URLs using customizable proxies. Supports LinkedIn, Indeed, StepStone, We Work Remotely, and Arbeitnow.
- 🚀 **Hybrid LLM Engine**: "Race Mode" runs local (Ollama) and remote (Groq/OpenRouter) models in parallel for maximum speed.
- 📄 **PDF Export**: Professional PDF format with embedded photo styling and multiple layout options (single-column, two-column).
- 🎨 **Modern UI**: Beautiful, responsive SvelteKit interface.
- 🐳 **Docker Ready** : Complete multi-service architecture.

## Architecture

```
┌─────────────┐
│   Certbot   │
└──────┬──────┘
       │ SSL
       ▼
┌─────────────┐                                      ┌─────────────┐
│    Nginx    │                                 ┌───▶│   Ollama    │
│  (Gateway)  │         ┌─────────────┐         │    │   (Local)   │
└───┬──────┬──┘         │   FastAPI   │         │    └─────────────┘
    │      └───────────▶│   Backend   │─────────┤
    ▼                   └─────┬───────┘         │    ┌─────────────┐
┌─────────────┐               │                 ├───▶│    Groq     │
│  SvelteKit  │               │                 │    │  (Primary)  │
│  Frontend   │               ▼                 │    └─────────────┘
└─────────────┘         ┌─────────────┐         │    ┌─────────────┐
                        │ PostgreSQL  │         └───▶│ OpenRouter  │
                        │  Database   │              │ (Failover)  │
                        └─────────────┘              └─────────────┘
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

```bash
git clone git@github.com:remitoudic/job_wizard.git
cd job_wizard

# Start services
./scripts/start_locally.sh

# First time: pull the Ollama model
docker exec jobwizard-ollama ollama pull llama3.2:1b
```

**Access**: http://localhost:5173

📖 **Full Development & Deployment Guide**: See [DEVELOPMENT.md](DEVELOPMENT.md) for complete instructions on local setup, environment variables, testing, and production deployment.

## Usage

1. Open http://localhost:5173 in your browser
2. Paste a job description URL (LinkedIn, Indeed, etc.) or paste text manually
3. Upload your CV/PDF for context
4. Click "Generate Cover Letter" (Watch the race between AI models!)
5. Review the AI-generated content
6. Download your PDF

## Troubleshooting

- **Ollama model not found?** Run `docker exec jobwizard-ollama ollama pull llama3.2:1b`
- **Scraping failed?** Check `proxies.json` or ensure the target URL is accessible.
- **Race mode issues?** Ensure at least one remote API key is set in `.env`.

## License

MIT


