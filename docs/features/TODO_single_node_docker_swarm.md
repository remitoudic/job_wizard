# Feature Spec: Single-Node Docker Swarm Migration

## 1. Description
This feature updates the production infrastructure for Job Wizard from standard **Docker Compose** to **Single-Node Docker Swarm**.

### Why This Change Matters & What It Brings:
1. **Zero-Downtime Rolling Updates**:
   - Using `docker stack deploy` with `order: start-first`, new container instances are built and launched in parallel before terminating old ones.
   - Swarm waits for container healthchecks (`/health` returning 200 OK) before routing web traffic to the updated container and stopping the old instance.
2. **Self-Healing & Desired State Enforcement**:
   - Swarm continuously monitors task states and automatically reschedules crashed or unhealthy containers to maintain configured replica counts.
3. **Docker Secret Management**:
   - Sensitive credentials (`POSTGRES_PASSWORD`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `LOGFIRE_TOKEN`, `LLAMA_CLOUD_API_KEY`) are encrypted at rest in Swarm's Raft database and mounted in-memory (`/run/secrets/`) inside container runtimes instead of plain-text `.env` files on disk.
4. **Declarative Stack Management**:
   - Unifies deployment workflows into `docker stack deploy -c docker-compose.prod.yml jobwizard`.

---

## 2. Specifications

### A. Infrastructure & Swarm Initialization
- **Swarm Init**: `deploy_production.sh` checks `docker info --format '{{.Swarm.LocalNodeState}}'`. If `inactive`, it executes `docker swarm init --advertise-addr 127.0.0.1`.
- **Overlay Networking**: Service network `jobwizard-network` configured with `driver: overlay` (attachable) for Swarm service routing and ingress load balancing.

### B. Docker Compose / Stack Configuration (`docker-compose.prod.yml`)
- **Deploy Config**:
  - `backend` and `frontend`: Add `deploy.replicas: 1`, `deploy.update_config.order: start-first`, `deploy.update_config.failure_action: rollback`, `deploy.update_config.delay: 5s`.
  - `postgres`, `ollama`, `temporal`, `worker`: Add `deploy.restart_policy.condition: on-failure`.
- **Healthchecks**: Ensure healthchecks are enabled on `backend` (`/health`), `frontend` (`/health`), `postgres` (`pg_isready`), and `ollama` (`ollama list`).

### C. Secret Management Integration
- Define Docker Secrets in Swarm for sensitive environment variables.
- Applications read credentials from `/run/secrets/<secret_name>` with fallback to environment variables for backward compatibility.

### D. Backup Script Adaptation (`scripts/backup-db.sh`)
- Update `scripts/backup-db.sh` container discovery to detect Swarm task containers (`jobwizard_postgres.1.*` as well as `jobwizard-postgres-prod`).

### E. Deployment Script Updates (`scripts/deploy_production.sh` & `scripts/update-production.sh`)
- Pre-flight automated database backup via `scripts/backup-db.sh`.
- Swarm state verification and stack deployment via `docker stack deploy -c docker-compose.prod.yml jobwizard`.
- Automated post-deploy status check via `docker stack services jobwizard` and `docker service ps jobwizard_backend`.

---

## 3. Validation Criteria

### Automated Verification
- **Database Backup**: Executing `./scripts/backup-db.sh` produces a valid, non-empty SQL dump in `services/backups/jobwizard_YYYYMMDD_HHMMSS.sql`.
- **Swarm Stack Deployment**: `docker stack deploy -c docker-compose.prod.yml jobwizard` deploys all 8 services without errors.
- **Health Check Verification**: `docker service ls` shows `REPLICAS 1/1` (or `2/2`) for all services.
- **Application Test Suite**: `bun run test --run` passes cleanly.

### Manual Verification
1. **Zero-Downtime Update**: Trigger a stack update while continuously pinging `http://localhost/health` or `https://job-vite.com/health`. Verify HTTP 200 OK responses with zero dropped requests.
2. **Secret Verification**: Verify credentials mounted under `/run/secrets/` in the `backend` container are accessible.
3. **Database Seeding Verification**: Run `docker exec $(docker ps -q -f name=jobwizard_backend) uv run python scripts/seed_user.py` and confirm clean execution.
