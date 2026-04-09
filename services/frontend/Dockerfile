FROM node:20-alpine AS development

WORKDIR /app

# Install bun (package manager/runtime) for development
RUN apk add --no-cache curl ca-certificates bash \
	&& curl -fsSL https://bun.sh/install | bash \
	&& ln -s /root/.bun/bin/bun /usr/local/bin/bun

# Copy package files
COPY package*.json ./

# Install dependencies with bun
RUN bun install

# Copy source code
COPY . .

# Expose ports
EXPOSE 3000 5173

# Development command using bun
CMD ["bun", "run", "dev", "--", "--host", "0.0.0.0"]

# Production build stage
FROM node:20-alpine AS builder

WORKDIR /app
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Install bun in builder stage to run installs and builds
RUN apk add --no-cache curl ca-certificates bash \
	&& curl -fsSL https://bun.sh/install | bash \
	&& ln -s /root/.bun/bin/bun /usr/local/bin/bun

COPY package*.json ./
RUN bun install

COPY . .
RUN bun run build

# Production stage
FROM oven/bun:alpine AS production

WORKDIR /app

COPY --from=builder /app/build ./build
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/start.sh ./

# Install production dependencies with bun (bun is present in this image)
RUN bun install --production || true

RUN chmod +x start.sh

EXPOSE 3000

# Use the simple start script
CMD ["./start.sh"]
