# Frontend Development Dockerfile
FROM node:22-alpine

# Accept build argument for pnpm store path
ARG PNPM_STORE_PATH=/root/.local/share/pnpm/store

# Install pnpm at specific version (matching package.json)
RUN corepack enable && corepack install -g pnpm@10.26.2

RUN pnpm config set store-dir ${PNPM_STORE_PATH}

# Set working directory
WORKDIR /app

# Copy frontend source code
COPY frontend ./frontend

# Install dependencies
RUN sh -c "cd /app/frontend && pnpm install --frozen-lockfile"

# Accept backend URLs as build args (baked into Next.js client bundle at build time)
ARG NEXT_PUBLIC_BACKEND_BASE_URL
ARG NEXT_PUBLIC_LANGGRAPH_BASE_URL
ENV NEXT_PUBLIC_BACKEND_BASE_URL=${NEXT_PUBLIC_BACKEND_BASE_URL}
ENV NEXT_PUBLIC_LANGGRAPH_BASE_URL=${NEXT_PUBLIC_LANGGRAPH_BASE_URL}
ENV SKIP_ENV_VALIDATION=1

RUN sh -c "cd /app/frontend && pnpm build"

# Expose Next.js port
EXPOSE 3000

CMD ["sh", "-c", "cd /app/frontend && pnpm start"]
