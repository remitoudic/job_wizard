# Job Wizard - Production Deployment Guide

This guide explains how to deploy Job Wizard to your production server.

## 🎯 Production Architecture

In production, nginx acts as a reverse proxy and is the **only service exposed to the internet**:

```
Internet (Port 80) → Nginx → Frontend (internal)
                   ↓
                   → Backend API (internal)
                   ↓
                   → PostgreSQL (internal)
                   ↓
                   → Ollama (internal)
```

**Security Benefits:**
- ✅ Users only see clean URLs (no port numbers)
- ✅ Internal services (database, LLM) are not directly accessible
- ✅ Single entry point for easier security management
- ✅ Ready for SSL/HTTPS when you add a domain

## 📋 Prerequisites

1. **Production Server** with:
   - Docker and Docker Compose installed
   - Ports 80 and 443 open in firewall
   - At least 4GB RAM recommended
   - Git installed

2. **Server IP Address**
   - You'll need your server's public IP address
   - Run on server: `curl ifconfig.me`

## 🚀 Deployment Steps

### 1. Copy Project to Production Server

```bash
# On your production server
git clone <your-repo-url>
cd job_wizard
```

### 2. Configure Production Environment

```bash
# Create production environment file
cp .env.production.example .env.production

# Edit the file and update these critical values:
nano .env.production
```

**Required changes in `.env.production`:**

```bash
# Change this to a strong password!
POSTGRES_PASSWORD=your_strong_password_here

# Replace YOUR_SERVER_IP with your actual server IP
# Example: If your IP is 123.45.67.89
ORIGIN=http://123.45.67.89
VITE_API_URL=http://123.45.67.89/api
CORS_ORIGINS=http://123.45.67.89
```

**Optional but recommended:**
- `OPENROUTER_API_KEY` - For using cloud LLM instead of local Ollama
- `LOGFIRE_TOKEN` - For application monitoring and observability

### 3. Deploy to Production

```bash
# Make the deployment script executable (already done if you cloned)
chmod +x scripts/deploy_production.sh

# Run the deployment script
./scripts/deploy_production.sh
```

The script will:
- Check if Docker is running
- Validate your `.env.production` file exists
- Ask for confirmation before deploying
- Build and start all services
- Show service status

### 4. Verify Deployment

```bash
# Check all services are running
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check specific service logs
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f backend
```

### 5. Access Your Application

Open your browser and navigate to:
```
http://YOUR_SERVER_IP
```

Example: `http://123.45.67.89`

## 🔄 Common Operations

### View Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f backend
```

### Restart Services
```bash
# Restart all services
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
```

### Update and Redeploy
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build
```

### Stop Services
```bash
docker compose -f docker-compose.prod.yml down
```

### Stop and Remove Everything (including data)
```bash
# WARNING: This deletes your database!
docker compose -f docker-compose.prod.yml down -v
```

## 🌐 Adding a Domain Name (Future)

When you get a domain name, follow these steps:

### 1. Point Domain to Server
- Add an A record in your DNS settings pointing to your server IP
- Wait for DNS propagation (can take up to 48 hours)

### 2. Update Environment Variables

Edit `.env.production`:
```bash
# Change from IP to domain
ORIGIN=https://yourdomain.com
VITE_API_URL=https://yourdomain.com/api
CORS_ORIGINS=https://yourdomain.com
```

### 3. Add SSL Certificate

You can use Let's Encrypt for free SSL certificates:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com
```

### 4. Update Nginx Configuration

Edit `nginx/nginx.conf` and uncomment the HTTPS server block (lines ~110-125), then update paths to your certificates.

### 5. Redeploy
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## 🔒 Security Best Practices

1. **Change Default Passwords**
   - Always use strong passwords in `.env.production`
   - Never use the example password `changeme123`

2. **Firewall Configuration**
   - Only open ports 80 (HTTP) and 443 (HTTPS)
   - Block all other ports (especially 5432, 8000, 11434)

3. **Regular Updates**
   - Keep Docker images updated
   - Pull latest code regularly
   - Monitor security advisories

4. **Backups**
   - Regularly backup the PostgreSQL data volume
   - Store backups securely off-server

5. **Environment Variables**
   - Never commit `.env.production` to git
   - Keep API keys and tokens secure

## 🐛 Troubleshooting

### Services won't start
```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# View error logs
docker compose -f docker-compose.prod.yml logs
```

### Can't access application
1. Check nginx is running: `docker compose -f docker-compose.prod.yml ps nginx`
2. Check firewall allows port 80: `sudo ufw status`
3. Verify CORS_ORIGINS matches your access URL
4. Check nginx logs: `docker compose -f docker-compose.prod.yml logs nginx`

### Database connection errors
1. Wait for postgres to be healthy: `docker compose -f docker-compose.prod.yml ps postgres`
2. Check DATABASE_URL in `.env.production` matches POSTGRES_PASSWORD
3. View postgres logs: `docker compose -f docker-compose.prod.yml logs postgres`

### Ollama not working
1. Check ollama is running: `docker compose -f docker-compose.prod.yml ps ollama`
2. Consider using OPENROUTER_API_KEY instead for more reliable cloud-based LLM
3. View ollama logs: `docker compose -f docker-compose.prod.yml logs ollama`

## 📊 Monitoring

Access service health:
```bash
# Check health endpoint
curl http://YOUR_SERVER_IP/health

# View all container stats
docker stats
```

If you configured LOGFIRE_TOKEN, you can view detailed observability at [logfire.pydantic.dev](https://logfire.pydantic.dev/).

## 🆘 Support

For issues or questions:
1. Check the logs first
2. Review this deployment guide
3. Check the main README.md for general documentation
4. Review Docker Compose documentation
