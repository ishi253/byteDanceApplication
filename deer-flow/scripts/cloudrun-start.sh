#!/usr/bin/env bash
# Start LangGraph, Gateway, and Nginx for a single Cloud Run container.
# Nginx listens on PORT (default 8080) and routes to gateway (8001) and langgraph (2024).
set -e
cd /app/backend

# Start LangGraph in background (port 2024)
uv run langgraph dev --no-browser --allow-blocking --host 0.0.0.0 --port 2024 &
LANGGRAPH_PID=$!

# Wait for LangGraph to be ready (root or /info often returns 200)
for i in $(seq 1 60); do
  if curl -sf -o /dev/null http://127.0.0.1:2024/ 2>/dev/null || curl -sf -o /dev/null http://127.0.0.1:2024/info 2>/dev/null; then
    break
  fi
  sleep 1
done

# Start Gateway in background (port 8001)
uv run uvicorn src.gateway.app:app --host 0.0.0.0 --port 8001 &
GATEWAY_PID=$!

# Wait for Gateway to be ready
for i in $(seq 1 30); do
  if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/health 2>/dev/null | grep -q 200; then
    break
  fi
  sleep 1
done

# Run nginx in foreground (holds container; listens on PORT from Cloud Run, default 8080)
exec nginx -g 'daemon off;' -c /etc/nginx/nginx.cloudrun.conf
