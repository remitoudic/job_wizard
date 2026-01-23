# Job Wizard Development Guide

Complete guide for developing and deploying the Job Wizard application.

## 📚 Table of Contents

- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)

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

## 💻 Local Development

### Prerequisites

- Docker Desktop installed and running
- Git
- 8GB+ RAM
- Terminal access

### Starting Services

Use the startup script:
```bash
./scripts/start_locally.sh
```

This automatically:
- Creates `.env` from `.env.example` if needed
- Sets localhost URLs
- Starts all Docker containers

### Accessing Services

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5434
- **Ollama**: http://localhost:11434

### Making Changes

All changes are hot-reloaded automatically:

**Backend** (`backend/app/`):
- FastAPI auto-reloads on file changes
- View logs: `docker compose logs -f backend`

**Frontend** (`frontend/src/`):
- Vite auto-reloads on file changes
- View logs: `docker compose logs -f frontend`

**Database** (`database/models.py`):
- Reset DB: `docker exec jobwizard-backend python backend/scripts/reset_db.py`

### Running Tests

```bash
# All tests
docker exec jobwizard-backend pytest tests/ -v

# Specific tests
docker exec jobwizard-backend pytest tests/test_ollama.py -v

# With output
docker exec jobwizard-backend pytest tests/ -v -s
```

### Stopping Services

**If running in foreground** (attached mode):
- Press `Ctrl+C`

**If running in background** (detached mode):
```bash
docker compose down
```

## 🌐 Production Deployment

### The Workflow

```
[Your Laptop]              [GitHub]              [Production Server]
     │                        │                         │
     ├─ Make changes          │                         │
     ├─ Test locally          │                         │
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

### Deploying Changes

**1. Develop & test locally:**
```bash
# On your laptop
./scripts/start_locally.sh
# Make changes, test, verify
docker exec jobwizard-backend pytest tests/ -v
```

**2. Commit and push:**
```bash
git add .
git commit -m "Your change description"
git push origin main
```

**3. Update production:**
```bash
# SSH to server: ssh user@147.93.111.113
cd /root/job_wizard
./scripts/update-production.sh
```

The update script will:
1. ✅ Create database backup
2. ✅ Pull latest code
3. ✅ Rebuild containers
4. ✅ Run health checks
5. ✅ Rollback automatically if anything fails

### Manual Backup

```bash
./scripts/backup-db.sh
```

Backups are stored in `backups/` directory with timestamps.

### Rollback

If something goes wrong:
```bash
./scripts/rollback-production.sh
```

Or manually:
```bash
git log --oneline -5  # Find previous commit
git reset --hard <commit-hash>
docker compose up -d --build
```

## 🔄 Development Workflow

### Day-to-Day Development

1. **Start your day**:
   ```bash
   cd job_wizard
   ./scripts/start_locally.sh
   ```

2. **Make changes**:
   - Edit code in your IDE
   - Changes auto-reload
   - Test in browser

3. **Run tests**:
   ```bash
   docker exec jobwizard-backend pytest tests/ -v
   ```

4. **Commit when ready**:
   ```bash
   git add .
   git commit -m "Descriptive message"
   ```

5. **End of day**:
   ```bash
   git push origin main
   docker compose down
   ```

### Deploying to Production

**When to deploy:**
- ✅ All tests passing
- ✅ Changes tested locally
- ✅ Committed and pushed to GitHub
- ✅ Not Friday afternoon 😉

**How to deploy:**
```bash
# On production server
./scripts/update-production.sh
```

**Monitor after deployment** (at least 15 minutes):
```bash
docker compose logs -f
docker ps
```

## 🛠 Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker info

# View logs
docker compose logs

# Restart specific service
docker compose restart backend
```

### Database issues

```bash
# Reset database (⚠️ deletes all data)
docker exec jobwizard-backend python backend/scripts/reset_db.py

# Restore from backup
docker exec -i jobwizard-postgres psql -U jobwizard -d jobwizard < backups/jobwizard_YYYYMMDD_HHMMSS.sql
```

### Ollama model not found

```bash
docker exec jobwizard-ollama ollama pull llama3.2:1b
```

### Port conflicts

```bash
# Check what's using a port
sudo lsof -i :8000
sudo lsof -i :5173

# Change ports in .env if needed
```

### Frontend can't connect to backend

**Local development:**
- Ensure `VITE_API_URL=http://localhost:8000` in `.env`

**Production:**
- Ensure `VITE_API_URL=http://147.93.111.113:8000` in `.env`

### Complete reset (⚠️ nuclear option)

```bash
docker compose down -v  # Deletes all data!
rm -rf node_modules/
./scripts/start_locally.sh  # or start_remote.sh on server
```

## 📋 Useful Commands

### Docker

```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View logs
docker compose logs -f
docker compose logs -f backend

# Restart service
docker compose restart backend

# Rebuild service
docker compose up -d --build backend

# Resource usage
docker stats

# Clean up
docker system prune -f
```

### Database

```bash
# Backup
./scripts/backup-db.sh

# List backups
ls -lh backups/

# Connect to database
docker exec -it jobwizard-postgres psql -U jobwizard -d jobwizard

# Reset database
docker exec jobwizard-backend python backend/scripts/reset_db.py
```

### Git

```bash
# Status
git status

# Recent commits
git log --oneline -10

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

## 🔐 Environment Variables

### Local Development (.env)
```bash
VITE_API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production (.env on server)
```bash
VITE_API_URL=http://147.93.111.113:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://147.93.111.113:5173,http://147.93.111.113:3000
```

**Security notes:**
- Never commit `.env` to git
- Keep production credentials secure
- Use different passwords for production

## 📞 Getting Help

### Check logs first
```bash
docker compose logs
```

### Run tests
```bash
docker exec jobwizard-backend pytest tests/ -v
```

### Verify configuration
```bash
cat .env
docker ps
```

## 🎯 Best Practices

- ✅ **Always test locally** before deploying
- ✅ **Run tests** before committing
- ✅ **Use descriptive commit messages**
- ✅ **Backup before major changes** (auto-done by update script)
- ✅ **Monitor after deployment**
- ✅ **Deploy early in the week**, not Friday
- ❌ Don't commit `.env` files
- ❌ Don't force push to main
- ❌ Don't skip testing
