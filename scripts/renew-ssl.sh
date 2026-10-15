#!/usr/bin/env bash
set -euo pipefail

# Renew Let's Encrypt certificates
docker run --rm \
  -v /root/job_wizard/services/certbot/conf:/etc/letsencrypt \
  -v /root/job_wizard/services/certbot/www:/var/www/certbot \
  certbot/certbot renew --quiet

# Reload Nginx inside Docker Swarm
NGINX_CONTAINER=$(docker ps -q -f name=jobwizard_nginx | head -n 1)
if [ -n "$NGINX_CONTAINER" ]; then
    docker exec "$NGINX_CONTAINER" nginx -s reload
else
    docker service update --force jobwizard_nginx
fi
