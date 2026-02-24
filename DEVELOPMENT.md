# Vite a Job! Development Guide

Complete guide for developing, testing, and deploying the Vite a Job! application.

## 📚 Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Local Development](#local-development)
- [Testing](#testing)
- [Debugging](#debugging)
- [Production Deployment](#production-deployment)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Useful Commands](#useful-commands)
- [Best Practices](#best-practices)

## 🚀 Quick Start

### For Local Development (Your Laptop)

```bash
# 1. Clone the repository
git clone git@github.com:remitoudic/job_wizard.git
cd job_wizard

# 2. Start all services
./scripts/start_locally.sh

# 3. Pull the Ollama model (first time only)
docker exec jobwizard-ollama ollama pull llama3.2:1b

# 4. Access the app
open http://localhost:5173
```

### For Production Updates (Server 147.93.111.113)

```bash
# Safe update with automatic backup and rollback
./scripts/update-production.sh
```

> [!TIP]
> See [DEPLOYMENT.md](DEPLOYMENT.md) for complete production deployment instructions.

## 🏗 Architecture Overview

Vite a Job! uses a modern microservices architecture with Docker Compose orchestration:

```
┌─────────────┐
│  SvelteKit  │ ← Frontend (Port 5173)
│  Frontend   │   • TailwindCSS styling
└──────┬──────┘   • Vite dev server
       │          • Hot reload enabled
       ▼
┌─────────────┐
│   FastAPI   │ ← Backend (Port 8000)
│   Backend   │   • Python 3.11 + uv
└──────┬──────┘   • Auto-reload on changes
       │          • Interactive API docs at /docs
       ├──────────────────────┐
       ▼                      ▼
┌─────────────┐        ┌─────────────┐
│ PostgreSQL  │        │   Ollama    │ ← Local LLM (Port 11434)
│  Database   │        │   (Local)   │   • llama3.2:1b model
└─────────────┘        └─────────────┘   • Optional (can use remote)
                              │
                              ├─────────────┐
                              ▼             ▼
                       ┌─────────────┐ ┌─────────────┐
                       │    Groq     │ │ OpenRouter  │
                       │  (Primary)  │ │ (Failover)  │
                       └─────────────┘ └─────────────┘
```

### Key Components

- **Frontend**: SvelteKit with TailwindCSS, handles UI and user interactions
- **Backend**: FastAPI REST API with modular parser architecture
- **Database**: PostgreSQL 16 for storing job data and user context
- **LLM Service**: Hybrid "race mode" - runs local and remote models in parallel
- **Parsers**: Modular job board parsers (LinkedIn, Indeed, StepStone, etc.)

### Project Structure

```
job_wizard/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── parsers/         # Modular parser architecture
│   │   │   │   ├── linkedin.py  # LinkedIn job parser
│   │   │   │   ├── indeed.py    # Indeed job parser
│   │   │   │   ├── stepstone.py # StepStone parser
│   │   │   │   └── ...
│   │   │   ├── job_parser.py    # Main parser entry point
│   │   │   ├── llm_service.py   # Hybrid race logic
│   │   │   └── pdf_service.py   # PDF generation
│   │   ├── routers/             # API endpoints
│   │   └── main.py              # FastAPI app
│   ├── database/                # SQLModel definitions
│   ├── tests/                   # Unit & integration tests
│   └── scripts/                 # Utility scripts
├── frontend/
│   ├── src/
│   │   ├── lib/components/      # Svelte components
│   │   ├── routes/              # SvelteKit routes
│   │   └── app.css              # Global styles
│   └── static/                  # Static assets
├── scripts/                     # Deployment & utility scripts
├── docker-compose.yml           # Local development
├── docker-compose.prod.yml      # Production config
└── DEVELOPMENT.md               # This file
```

## 💻 Local Development

### Prerequisites

- **Docker Desktop** installed and running
- **Git** for version control
- **8GB+ RAM** recommended
- **Terminal** access (bash/zsh)

### Starting Services

Use the startup script for the easiest setup:
```bash
./scripts/start_locally.sh
```

This automatically:
- ✅ Creates `.env` from `.env.example` if needed
- ✅ Sets localhost URLs for all services
- ✅ Starts all Docker containers in the correct order
- ✅ Waits for services to be healthy

**Manual start** (if you prefer):
```bash
# Copy environment file (first time only)
cp .env.example .env

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

### Accessing Services

Once started, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | Main application UI |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **PostgreSQL** | localhost:5434 | Database (user: jobwizard) |
| **Ollama** | http://localhost:11434 | Local LLM service |

### Making Changes

All changes are **hot-reloaded automatically** - no need to restart!

#### Backend Changes (`backend/app/`)
- FastAPI auto-reloads on file changes
- View logs: `docker compose logs -f backend`
- Check API docs: http://localhost:8000/docs

#### Frontend Changes (`frontend/src/`)
- Vite auto-reloads on file changes
- View logs: `docker compose logs -f frontend`
- Changes appear instantly in browser

#### Database Schema Changes (`database/models.py`)
After modifying models, reset the database:
```bash
docker exec jobwizard-backend python backend/scripts/reset_db.py
```

> [!WARNING]
> Resetting the database **deletes all data**. Use backups for production!

### Stopping Services

**If running in foreground** (attached mode):
- Press `Ctrl+C`

**If running in background** (detached mode):
```bash
docker compose down
```

**To also remove volumes** (⚠️ deletes database data):
```bash
docker compose down -v
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
docker exec jobwizard-backend pytest tests/ -v

# Run specific test file
docker exec jobwizard-backend pytest tests/integration/test_ollama.py -v

# Run with detailed output
docker exec jobwizard-backend pytest tests/ -v -s

# Run with coverage report
docker exec jobwizard-backend pytest tests/ --cov=app --cov-report=html
```

### Test Structure

```
backend/tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_parsers.py      # Parser logic tests
│   └── test_services.py     # Service layer tests
└── integration/             # Integration tests (slower, with dependencies)
    ├── test_ollama.py       # LLM integration tests
    └── test_api.py          # API endpoint tests
```

### Writing Tests

**Unit test example:**
```python
def test_linkedin_parser_extracts_title():
    """Test that LinkedIn parser correctly extracts job title."""
    html = '<h1 class="job-title">Software Engineer</h1>'
    parser = LinkedInParser()
    result = parser.parse_html(html)
    assert result.title == "Software Engineer"
```

**Integration test example:**
```python
@pytest.mark.integration
def test_generate_cover_letter_with_ollama():
    """Test end-to-end cover letter generation."""
    response = client.post("/api/generate", json={
        "job_description": "Python developer needed",
        "context": "I have 5 years of Python experience"
    })
    assert response.status_code == 200
    assert "cover_letter" in response.json()
```

### Test Best Practices

- ✅ Run tests before committing
- ✅ Write tests for new features
- ✅ Keep unit tests fast (< 1 second each)
- ✅ Use fixtures for common test data
- ✅ Mock external services (LLM APIs, web scraping)

## 🐛 Debugging

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend

# Last 100 lines
docker compose logs --tail=100 backend

# Filter by error level
docker compose logs backend | grep ERROR
```

### Interactive Debugging

**Backend (Python debugger):**
```python
# Add breakpoint in your code
import pdb; pdb.set_trace()

# Or use modern debugger
import ipdb; ipdb.set_trace()
```

Then attach to the container:
```bash
docker attach jobwizard-backend
```

**Database inspection:**
```bash
# Connect to PostgreSQL
docker exec -it jobwizard-postgres psql -U jobwizard -d jobwizard

# Useful SQL commands
\dt              # List tables
\d+ jobs         # Describe jobs table
SELECT * FROM jobs LIMIT 5;
```

### Common Debugging Scenarios

**Problem: Frontend can't reach backend**
```bash
# Check backend is running
docker ps | grep backend

# Check backend logs for errors
docker compose logs backend

# Verify VITE_API_URL in .env
cat .env | grep VITE_API_URL
```

**Problem: LLM generation fails**
```bash
# Check Ollama is running
docker exec jobwizard-ollama ollama list

# Test Ollama directly
docker exec jobwizard-ollama ollama run llama3.2:1b "Hello"

# Check API keys for remote providers
cat .env | grep -E "GROQ|OPENROUTER"
```

**Problem: Parser fails to extract job data**
```bash
# Enable debug logging in backend
# Add to .env: LOG_LEVEL=DEBUG

# Check parser logs
docker compose logs backend | grep -i parser

# Test parser manually in Python shell
docker exec -it jobwizard-backend python
>>> from app.services.parsers.linkedin import LinkedInParser
>>> parser = LinkedInParser()
>>> # Test your parsing logic
```

## 🌐 Production Deployment

### Quick Reference

```bash
# On production server (147.93.111.113)
cd /root/job_wizard
./scripts/update-production.sh
```

### The Deployment Workflow

```
[Your Laptop]              [GitHub]              [Production Server]
     │                        │                         │
     ├─ Make changes          │                         │
     ├─ Test locally          │                         │
     ├─ Run tests             │                         │
     ├─ Commit & push ───────>│                         │
     │                        │                         │
     │                        │<──── Pull changes ──────┤
     │                        │                         │
     │                        │         Backup DB ──────┤
     │                        │                         │
     │                        │      Rebuild & Start ───┤
     │                        │                         │
     │                        │       Health Checks ────┤
     │                        │                         │
     │                        │  ✅ Success / ❌ Rollback ┤
```

### Step-by-Step Deployment

**1. Develop & test locally:**
```bash
# On your laptop
./scripts/start_locally.sh

# Make your changes
# Test in browser at http://localhost:5173

# Run tests
docker exec jobwizard-backend pytest tests/ -v
```

**2. Commit and push:**
```bash
git add .
git commit -m "feat: add new LinkedIn parser field"
git push origin main
```

**3. Update production:**
```bash
# SSH to server
ssh user@147.93.111.113

# Navigate to project
cd /root/job_wizard

# Run safe update script
./scripts/update-production.sh
```

The update script automatically:
1. ✅ Creates database backup (stored in `backups/`)
2. ✅ Pulls latest code from GitHub
3. ✅ Rebuilds Docker containers
4. ✅ Runs health checks
5. ✅ **Rolls back automatically** if anything fails

### Manual Operations

**Manual backup:**
```bash
./scripts/backup-db.sh
# Backup saved to: backups/jobwizard_YYYYMMDD_HHMMSS.sql
```

**List backups:**
```bash
ls -lh backups/
```

**Restore from backup:**
```bash
docker exec -i jobwizard-postgres psql -U jobwizard -d jobwizard < backups/jobwizard_20260215_120000.sql
```

**Manual rollback:**
```bash
git log --oneline -5  # Find previous commit
git reset --hard <commit-hash>
docker compose -f docker-compose.prod.yml up -d --build
```

> [!IMPORTANT]
> See [DEPLOYMENT.md](DEPLOYMENT.md) for complete production setup instructions, including initial deployment, SSL configuration, and domain setup.

## 🔄 Development Workflow

### Daily Development Routine

**1. Start your day:**
```bash
cd job_wizard
./scripts/start_locally.sh
```

**2. Make changes:**
- Edit code in your IDE
- Changes auto-reload in browser
- Test features manually

**3. Run tests:**
```bash
docker exec jobwizard-backend pytest tests/ -v
```

**4. Commit when ready:**
```bash
git add .
git commit -m "feat: descriptive message"
```

**5. End of day:**
```bash
git push origin main
docker compose down
```

### When to Deploy to Production

Deploy when:
- ✅ All tests passing locally
- ✅ Changes tested manually in browser
- ✅ Code committed and pushed to GitHub
- ✅ During business hours (not late Friday!)
- ✅ You can monitor for 15+ minutes after

**Don't deploy when:**
- ❌ Tests are failing
- ❌ You haven't tested locally
- ❌ It's Friday evening
- ❌ You can't monitor afterward

### Monitoring After Deployment

```bash
# Watch logs for 15+ minutes
docker compose -f docker-compose.prod.yml logs -f

# Check service health
docker ps
curl http://147.93.111.113/health

# Monitor resource usage
docker stats
```

## 🛠 Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker info

# View all logs
docker compose logs

# Check specific service
docker compose logs backend

# Restart specific service
docker compose restart backend

# Nuclear option: full restart
docker compose down
docker compose up -d
```

### Database Issues

**Connection errors:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# View PostgreSQL logs
docker compose logs postgres

# Verify connection settings
cat .env | grep DATABASE_URL
```

**Reset database (⚠️ deletes all data):**
```bash
docker exec jobwizard-backend python backend/scripts/reset_db.py
```

**Restore from backup:**
```bash
docker exec -i jobwizard-postgres psql -U jobwizard -d jobwizard < backups/jobwizard_YYYYMMDD_HHMMSS.sql
```

### Ollama Model Issues

```bash
# Check if model is downloaded
docker exec jobwizard-ollama ollama list

# Pull the model
docker exec jobwizard-ollama ollama pull llama3.2:1b

# Test model directly
docker exec jobwizard-ollama ollama run llama3.2:1b "Write a test message"
```

### Port Conflicts

```bash
# Check what's using a port
sudo lsof -i :8000
sudo lsof -i :5173
sudo lsof -i :5434

# Kill process on port (if needed)
sudo kill -9 $(lsof -t -i:8000)

# Or change ports in .env
```

### Frontend Can't Connect to Backend

**Local development:**
```bash
# Verify .env settings
cat .env | grep VITE_API_URL
# Should be: VITE_API_URL=http://localhost:8000

# Check CORS settings
cat .env | grep CORS_ORIGINS
# Should include: http://localhost:5173
```

**Production:**
```bash
# Verify .env.production settings
cat .env.production | grep VITE_API_URL
# Should be: VITE_API_URL=http://147.93.111.113:8000
```

### Complete Reset (⚠️ Nuclear Option)

```bash
# Stop everything and delete all data
docker compose down -v

# Remove node modules (if frontend issues)
rm -rf frontend/node_modules/

# Start fresh
./scripts/start_locally.sh
```

## 📋 Useful Commands

### Docker Commands

```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View logs (follow mode)
docker compose logs -f
docker compose logs -f backend

# Restart service
docker compose restart backend

# Rebuild specific service
docker compose up -d --build backend

# Rebuild all services
docker compose up -d --build

# Resource usage
docker stats

# Clean up unused images/containers
docker system prune -f

# Clean up everything (⚠️ nuclear)
docker system prune -a --volumes
```

### Database Commands

```bash
# Create backup
./scripts/backup-db.sh

# List backups
ls -lh backups/

# Connect to database
docker exec -it jobwizard-postgres psql -U jobwizard -d jobwizard

# Useful SQL commands (once connected)
\dt              # List all tables
\d+ jobs         # Describe jobs table
\du              # List users
\l               # List databases
SELECT * FROM jobs LIMIT 5;
\q               # Quit

# Reset database
docker exec jobwizard-backend python backend/scripts/reset_db.py

# Restore from backup
docker exec -i jobwizard-postgres psql -U jobwizard -d jobwizard < backups/jobwizard_YYYYMMDD_HHMMSS.sql
```

### Git Commands

```bash
# Check status
git status

# View recent commits
git log --oneline -10

# View changes
git diff

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# View file history
git log --follow -p -- path/to/file

# Create branch
git checkout -b feature/new-parser

# Switch branches
git checkout main
```

### Python/Backend Commands

```bash
# Run Python shell in backend container
docker exec -it jobwizard-backend python

# Run specific script
docker exec jobwizard-backend python backend/scripts/reset_db.py

# Install new dependency (using uv)
docker exec jobwizard-backend uv add requests

# Format code
docker exec jobwizard-backend ruff format .

# Lint code
docker exec jobwizard-backend ruff check .
```

### Frontend Commands

```bash
# Install new dependency
docker exec jobwizard-frontend bun add svelte-package

# Build for production
docker exec jobwizard-frontend bun run build

# Run linter
docker exec jobwizard-frontend bun run lint
```

## 🔐 Environment Variables

### Local Development (`.env`)

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Database
DATABASE_URL=postgresql://jobwizard:jobwizard@postgres:5432/jobwizard
POSTGRES_PASSWORD=jobwizard

# LLM Providers (optional for local dev)
GROQ_API_KEY=your_groq_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Ollama (local LLM)
OLLAMA_BASE_URL=http://ollama:11434
```

### Production (`.env.production` on server)

```bash
# API Configuration
VITE_API_URL=http://147.93.111.113:8000
CORS_ORIGINS=http://147.93.111.113:5173,http://147.93.111.113:3000

# Database (use strong password!)
DATABASE_URL=postgresql://jobwizard:STRONG_PASSWORD@postgres:5432/jobwizard
POSTGRES_PASSWORD=STRONG_PASSWORD

# LLM Providers (recommended for production)
GROQ_API_KEY=your_groq_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Monitoring (optional)
LOGFIRE_TOKEN=your_logfire_token_here
```

> [!CAUTION]
> **Never commit `.env` files to git!** They contain sensitive credentials.

### Security Best Practices

- ✅ Use strong, unique passwords for production
- ✅ Rotate API keys regularly
- ✅ Use different credentials for dev vs production
- ✅ Keep `.env` files in `.gitignore`
- ❌ Never commit `.env` to version control
- ❌ Never share credentials in chat/email

## 📞 Getting Help

### Debugging Checklist

1. **Check logs first:**
   ```bash
   docker compose logs
   ```

2. **Run tests:**
   ```bash
   docker exec jobwizard-backend pytest tests/ -v
   ```

3. **Verify configuration:**
   ```bash
   cat .env
   docker ps
   ```

4. **Check service health:**
   ```bash
   curl http://localhost:8000/health
   ```

### Additional Resources

- **[README.md](README.md)** - Project overview and features
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete production deployment guide
- **[USER_TESTING_GUIDE.md](USER_TESTING_GUIDE.md)** - User testing instructions
- **API Documentation** - http://localhost:8000/docs (when running)

## 🎯 Best Practices

### Code Quality

- ✅ **Write tests** for new features
- ✅ **Run tests** before committing
- ✅ **Use type hints** in Python code
- ✅ **Follow naming conventions** (snake_case for Python, camelCase for JS)
- ✅ **Keep functions small** and focused
- ✅ **Document complex logic** with comments

### Git Workflow

- ✅ **Use descriptive commit messages**
  - Good: `feat: add StepStone parser with proxy support`
  - Bad: `fix stuff`
- ✅ **Commit frequently** with logical chunks
- ✅ **Pull before push** to avoid conflicts
- ✅ **Review changes** before committing (`git diff`)
- ❌ Don't commit `.env` files
- ❌ Don't force push to main
- ❌ Don't commit commented-out code

### Deployment

- ✅ **Always test locally** before deploying
- ✅ **Deploy during business hours** when you can monitor
- ✅ **Monitor for 15+ minutes** after deployment
- ✅ **Have rollback plan** ready
- ✅ **Backup before major changes** (auto-done by update script)
- ❌ Don't deploy on Friday afternoon
- ❌ Don't deploy without testing
- ❌ Don't deploy if you can't monitor

### Development

- ✅ **Use hot reload** - no need to restart services
- ✅ **Check API docs** at http://localhost:8000/docs
- ✅ **Use Docker logs** for debugging
- ✅ **Keep dependencies updated** regularly
- ✅ **Document new features** in README
- ❌ Don't edit code inside containers
- ❌ Don't skip the startup script
- ❌ Don't ignore test failures

---

**Happy coding! 🚀**

For questions or issues, check the logs first, then review this guide and other documentation files.
