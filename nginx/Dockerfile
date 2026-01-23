FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create log directory
RUN mkdir -p /var/log/nginx

# Expose only HTTP port (and HTTPS when configured)
EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
