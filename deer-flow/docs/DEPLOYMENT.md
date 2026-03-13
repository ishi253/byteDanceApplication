# Deployment Plan: Vercel (Frontend) + GCP (Backend)

This document describes how to deploy the DeerFlow GTM Research application with the **frontend on Vercel** and the **backend on Google Cloud Platform (GCP)**.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Users / Browsers                               │
└─────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Vercel                                                                  │
│  Next.js frontend (deer-flow/frontend)                                   │
│  - Static + SSR                                                          │
│  - Env: NEXT_PUBLIC_BACKEND_BASE_URL, NEXT_PUBLIC_LANGGRAPH_BASE_URL     │
└─────────────────────────────────────────────────────────────────────────┘
                    │
                    │  Same origin or single API URL
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  GCP Cloud Run (single service)                                          │
│  One container: Nginx (PORT 8080) → Gateway (8001) + LangGraph (2024)   │
│  - /api/langgraph/*  → LangGraph                                        │
│  - /api/*            → Gateway (uploads, threads, models, skills, etc.) │
└─────────────────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│  Cloud SQL    │       │ Secret Manager│
│  PostgreSQL   │       │ (API keys)    │
│  (checkpointer)       │               │
└───────────────┘       └───────────────┘
```

---

## Project IDs (this deployment)

| Service | ID / URL |
|--------|----------|
| **GCP** project ID | `bytedance-490020` |
| **GCP** project number | `1079717528757` |
| **Vercel** project ID | `prj_59Dc4Q5vyxzo015tkBZt2ZvE8T4F` |
| **Vercel** app URL | `https://byte-dance-application.vercel.app` |

---

## Prerequisites

- **Vercel** account and CLI (`npm i -g vercel`) or GitHub integration.
- **GCP** project with billing enabled.
- **gcloud** CLI installed and authenticated (`gcloud auth login`, `gcloud config set project bytedance-490020`).
- **Docker** (for building the backend image locally or use Cloud Build).

---

## Checkpointer for deployment (summary)

For production you must use **PostgreSQL** so conversation state survives restarts and works with Cloud Run.

| What | Value |
|------|--------|
| **Type** | `postgres` |
| **Connection** | Env var `DEERFLOW_PG_DSN` (set from Secret Manager or Cloud Run env). |
| **Config file** | Image provides `config.cloudrun.yaml` with `checkpointer.type: postgres` and `connection_string: $DEERFLOW_PG_DSN`. |

**What you need to do:**

1. Create a **Cloud SQL** Postgres instance, database, and user (see [1.3](#13-cloud-sql-postgresql-for-checkpointer)).
2. Build the **DSN** (e.g. `postgresql://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE`) and store it in **Secret Manager** (e.g. secret name `DEERFLOW_PG_DSN`).
3. When deploying Cloud Run: pass `DEERFLOW_PG_DSN` from that secret, set `DEER_FLOW_CONFIG_PATH=/app/config.cloudrun.yaml`, and attach the instance with `--add-cloudsql-instances`.

Without this, the app uses the default in-image config (sqlite), which is not suitable for Cloud Run (ephemeral filesystem, no persistence across revisions).

---

## Phase 1: GCP Backend

Set your GCP project first (run once):

```bash
gcloud config set project bytedance-490020
```

### 1.1 Enable APIs

```bash
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com
```

### 1.2 Create Secrets (Secret Manager)

Store API keys and DB connection so Cloud Run can use them.

```bash
# Required for GTM (Tavily search)
echo -n "YOUR_TAVILY_API_KEY" | gcloud secrets create tavily-api-key --data-file=-

# LLM (e.g. DeepSeek)
echo -n "YOUR_DEEPSEEK_API_KEY" | gcloud secrets create deepseek-api-key --data-file=-

# Optional: Jina, Firecrawl, etc.
# echo -n "..." | gcloud secrets create jina-api-key --data-file=-
```

Grant Cloud Run’s service account access to secrets:

```bash
SA="1079717528757-compute@developer.gserviceaccount.com"
for s in tavily-api-key deepseek-api-key DEERFLOW_PG_DSN; do
  gcloud secrets add-iam-policy-binding $s --member="serviceAccount:${SA}" --role="roles/secretmanager.secretAccessor"
done
```

### 1.3 Cloud SQL (PostgreSQL) for checkpointer

Persistent conversation state requires a Postgres checkpointer.

```bash
# Create instance (adjust region/name as needed)
gcloud sql instances create deerflow-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create deerflow --instance=deerflow-db

# Create user and set password (store password securely)
gcloud sql users create deerflow --instance=deerflow-db --password=YOUR_DB_PASSWORD
```

Get the connection name and build the DSN:

```bash
# Connection name for Cloud Run (for this project: bytedance-490020:us-central1:deerflow-db)
gcloud sql instances describe deerflow-db --format='value(connectionName)'
# DSN format: postgresql://deerflow:YOUR_DB_PASSWORD@/deerflow?host=/cloudsql/bytedance-490020:us-central1:deerflow-db
```

Store the full DSN in Secret Manager (recommended) or pass as env:

```bash
# Replace YOUR_DB_PASSWORD with the password you set for user deerflow
echo -n "postgresql://deerflow:YOUR_DB_PASSWORD@/deerflow?host=/cloudsql/bytedance-490020:us-central1:deerflow-db" | \
  gcloud secrets create DEERFLOW_PG_DSN --data-file=-
```

### 1.4 Build and push backend image

From the **repository root** (run from the directory that contains `deer-flow/` or from `deer-flow/` if the repo root is `deer-flow`):

```bash
cd deer-flow
docker build -f docker/Dockerfile.cloudrun -t gcr.io/bytedance-490020/deer-flow-backend:latest .
docker push gcr.io/bytedance-490020/deer-flow-backend:latest
```

Or use Cloud Build (run from inside `deer-flow/`):

```bash
cd deer-flow
gcloud config set project bytedance-490020
gcloud builds submit --config cloudbuild.yaml .
```

### 1.5 Deploy to Cloud Run

- **Single service** (recommended): one container runs Nginx + Gateway + LangGraph; Nginx listens on `PORT` (8080).

```bash
gcloud run deploy deer-flow-backend \
  --image gcr.io/bytedance-490020/deer-flow-backend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "CORS_ORIGINS=https://byte-dance-application.vercel.app,https://byte-dance-application-*.vercel.app,DEER_FLOW_CONFIG_PATH=/app/config.cloudrun.yaml" \
  --set-secrets "TAVILY_API_KEY=tavily-api-key:latest,DEEPSEEK_API_KEY=deepseek-api-key:latest,DEERFLOW_PG_DSN=DEERFLOW_PG_DSN:latest" \
  --add-cloudsql-instances bytedance-490020:us-central1:deerflow-db \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 600
```

**Checkpointer:** The command above uses `config.cloudrun.yaml` (Postgres) and injects `DEERFLOW_PG_DSN` from the Secret Manager secret named `DEERFLOW_PG_DSN`. Ensure that secret exists and the Cloud Run service account has `roles/secretmanager.secretAccessor` on it (see [1.2](#12-create-secrets-secret-manager)); also grant `roles/cloudsql.client` if using a private Cloud SQL instance. The instance name in `--add-cloudsql-instances` must match your Cloud SQL instance (e.g. `deerflow-db`).

### 1.6 Get backend URL

After deploy:

```bash
gcloud run services describe deer-flow-backend --region us-central1 --format='value(status.url)'
```

Copy the URL (e.g. `https://deer-flow-backend-xxxxx-uc.a.run.app`) and set it in Vercel as below.

---

## Phase 2: Vercel Frontend

### 2.1 Connect repository and set Root Directory

If you link the repo in the **Vercel dashboard** (Git integration), you **must** set the **Root Directory** so Vercel builds the Next.js app instead of the repo root. Otherwise you get **404 NOT_FOUND** on the deployed URL.

1. In Vercel: **Project → Settings → General**.
2. Under **Root Directory**, click **Edit**, set to **`deer-flow/frontend`**, and save.
3. Redeploy (e.g. trigger a new deployment from the Deployments tab or push a commit).

If you deploy with the **CLI** from the app directory, Root Directory is implicit:

- From repo root: `cd deer-flow/frontend && vercel` (or `vercel --prod`).

### 2.2 Environment variables (Vercel)

In **Vercel** → Project **byte-dance-application** (ID `prj_59Dc4Q5vyxzo015tkBZt2ZvE8T4F`) → **Settings → Environment Variables**, set:

| Variable | Value | Environment |
|----------|--------|-------------|
| `NEXT_PUBLIC_BACKEND_BASE_URL` | *(paste the URL from step 1.6, e.g. `https://deer-flow-backend-xxxxx-uc.a.run.app`)* | Production, Preview |
| `NEXT_PUBLIC_LANGGRAPH_BASE_URL` | *(same URL as above)* | Production, Preview |
| `BETTER_AUTH_SECRET` | (optional) e.g. `openssl rand -hex 32` | Production |

Both `*_BASE_URL` must be the **same** Cloud Run URL from step 1.6 so the frontend sends:

- Gateway: `NEXT_PUBLIC_BACKEND_BASE_URL` + `/api/*`
- LangGraph: `NEXT_PUBLIC_LANGGRAPH_BASE_URL` + `/api/langgraph` (SDK uses same origin when URLs match).

### 2.3 Deploy

- **Git**: Push to the linked branch; Vercel builds and deploys automatically.  
- **CLI**: From `deer-flow/frontend`: `vercel --prod`.

Build uses `pnpm build` (see `vercel.json`). Ensure the repo has `pnpm-lock.yaml` and that Vercel uses pnpm.

### 2.4 Custom domain (optional)

If you add a custom domain in Vercel, update **GCP CORS** and redeploy:

```bash
gcloud run services update deer-flow-backend --region us-central1 \
  --set-env-vars "CORS_ORIGINS=https://byte-dance-application.vercel.app,https://byte-dance-application-*.vercel.app,https://www.yourdomain.com,DEER_FLOW_CONFIG_PATH=/app/config.cloudrun.yaml"
```

---

## Phase 3: Post-deploy checks

1. **Health** — Replace `YOUR_CLOUD_RUN_URL` with the URL from step 1.6:
   ```bash
   curl https://YOUR_CLOUD_RUN_URL/health
   ```
   Expect 200.

2. **Frontend**: Open https://byte-dance-application.vercel.app; create a thread and send a GTM topic (e.g. “GTM analysis for EV charging in Europe”).
3. **Streaming**: Confirm chat streams and artifacts appear.
4. **Uploads + RAG**: Upload a PDF, then ask a question that should use RAG.

---

## Configuration summary

### Backend (Cloud Run)

- **Config file**: `config.yaml` is baked into the image; use env vars for secrets (e.g. `$DEEPSEEK_API_KEY`, `$TAVILY_API_KEY`).  
- **Checkpointer**: Set `checkpointer.connection_string` via `DEERFLOW_PG_DSN` (or equivalent) and Cloud SQL.  
- **CORS**: Set `CORS_ORIGINS` to your Vercel (and custom) frontend origins.  
- **Extensions**: `extensions_config.json` is copied from the example in the image; for production you can build with a custom file or mount it if supported.

### Frontend (Vercel)

- **API URLs**: Both `NEXT_PUBLIC_BACKEND_BASE_URL` and `NEXT_PUBLIC_LANGGRAPH_BASE_URL` must point to the same Cloud Run URL.  
- **Auth**: If you enable better-auth later, set `BETTER_AUTH_SECRET` in Vercel.

---

## Alternative: Two Cloud Run services + Load Balancer

If you prefer to run **Gateway** and **LangGraph** as separate services:

1. Build two images: one that runs only the Gateway (port 8001), one that runs only the LangGraph server (port 2024).  
2. Deploy two Cloud Run services.  
3. Create an **HTTP(S) Load Balancer** with a **URL map**:
   - `/api/langgraph/*` → LangGraph service  
   - `/api/*` → Gateway service  
4. Point the frontend’s `NEXT_PUBLIC_*` URLs to the load balancer URL.

The single-container approach (Nginx + Gateway + LangGraph) is simpler to operate and is recommended unless you need to scale or secure the two backends independently.

---

## Files added for deployment

| Path | Purpose |
|------|--------|
| `frontend/vercel.json` | Vercel framework and build settings |
| `frontend/.env.production.example` | Example production env for frontend |
| `docker/Dockerfile.cloudrun` | Single-container backend for Cloud Run |
| `docker/nginx/nginx.cloudrun.conf` | Nginx routing for Cloud Run (port 8080) |
| `scripts/cloudrun-start.sh` | Starts LangGraph, Gateway, then Nginx in one container |
| `docs/DEPLOYMENT.md` | This deployment plan |

---

## Troubleshooting

- **404 NOT_FOUND on Vercel**: The app lives in `deer-flow/frontend`, not at the repo root. In Vercel → **Settings → General**, set **Root Directory** to `deer-flow/frontend`, then redeploy.  
- **CORS errors**: Ensure `CORS_ORIGINS` on Cloud Run includes the exact Vercel origin (and preview URLs if needed).  
- **502 / timeouts**: Increase Cloud Run `--timeout` (e.g. 600s for long GTM runs) and check LangGraph/Gateway logs in GCP Console → Logging.  
- **Checkpointer errors**: Verify Cloud SQL connection name, DSN format, and that the Cloud Run service account has Cloud SQL Client role if using private IP.  
- **Missing env in build**: Next.js bakes `NEXT_PUBLIC_*` at build time; set them in Vercel before building.
