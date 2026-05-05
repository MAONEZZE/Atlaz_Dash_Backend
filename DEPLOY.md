# Deployment Guide — Easypanel

## Prerequisites

- Easypanel instance running
- Docker support enabled
- Environment variables prepared

## Step 1: Prepare Environment Variables

Copy `.env.example` to a secure location. Fill in all required variables:

```bash
GOOGLE_SHEETS_CREDENTIALS_JSON={"type":"service_account",...}
DEFAULT_SPREADSHEET_ID=your-spreadsheet-id
DATABASE_URL=postgresql://user:password@db-host:5432/database
N8N_STATISTICS_URL=https://n8n.learningbrands.cloud/webhook/statistic
CORS_ORIGINS=https://your-frontend.com,https://another-frontend.com
DEBUG_ROUTES_ENABLED=false
VITE_IMG_JACOB_TOKEN=
VITE_IMG_JONATHAN_TOKEN=
VITE_IMG_ALEX_TOKEN=
VITE_IMG_JENNIFER_TOKEN=
LOG_LEVEL=INFO
```

## Step 2: Build Docker Image

In Easypanel:

1. Go to **Services** → **Create Service**
2. Select **Docker Image**
3. Enter repository URL: `<your-git-repo-url>`
4. Select branch: `main`
5. Dockerfile path: `./Dockerfile`
6. Build context: `.`

Or build locally and push to registry:

```bash
docker build -t atlaz-dash-backend:latest .
docker tag atlaz-dash-backend:latest <your-registry>/atlaz-dash-backend:latest
docker push <your-registry>/atlaz-dash-backend:latest
```

## Step 3: Configure Service in Easypanel

1. **Image**: `<your-registry>/atlaz-dash-backend:latest` (or local image)
2. **Ports**: Map container port `8000` to service port `8000`
3. **Environment Variables**: Paste all variables from Step 1
4. **Health Check** (optional):
   - Path: `/health`
   - Port: `8000`
   - Interval: `30s`

## Step 4: Deploy

1. Click **Create Service**
2. Easypanel builds and runs the container
3. Monitor logs in **Service → Logs**

## Step 5: Verify Deployment

Test the health endpoint:

```bash
curl https://<your-easypanel-domain>/health
# Should return: {"status": "ok"}
```

Test Swagger docs:

```
https://<your-easypanel-domain>/doc
```

## Troubleshooting

### Port issues
- Ensure port 8000 is mapped correctly in Easypanel
- Check firewall rules

### Environment variable errors
- Verify all required vars are set (check logs)
- Ensure GOOGLE_SHEETS_CREDENTIALS_JSON is valid JSON (not escaped)

### Google Sheets access error
- Verify service account has read access to spreadsheet
- Check DEFAULT_SPREADSHEET_ID is correct
- Use debug route: `GET /debug/sheets/METAS/raw`

### Database connection error
- Verify DATABASE_URL connection string
- Ensure Supabase instance is running
- Check network connectivity from container to database

### n8n statistics timeout
- Verify N8N_STATISTICS_URL is accessible
- Check n8n webhook is active
- Service returns empty stats on timeout (safe fallback)

## Monitoring

Check logs in Easypanel dashboard:
- Look for `ERROR` or `WARNING` messages
- Verify startup: "Application startup complete"
- Monitor requests to health endpoint

## Updates

To deploy a new version:

1. Commit changes to `main`
2. Easypanel auto-rebuilds if configured for auto-deploy
3. Or manually trigger rebuild in Easypanel dashboard

## Rollback

Keep previous versions available in Easypanel:
1. Go to **Service → Versions**
2. Select previous version
3. Click **Rollback**
