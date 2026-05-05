# Next Steps to 100% Production Ready

## Immediate (Today)

### 1. Set Up Google Service Account Credentials

If you haven't already:

1. Create Google Cloud project
2. Enable Google Sheets API
3. Create Service Account
4. Download JSON credentials
5. Share spreadsheet with service account email
6. Get spreadsheet ID from URL

### 2. Prepare Environment Variables

Create `.env` file in project root:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
GOOGLE_SHEETS_CREDENTIALS_JSON={paste raw JSON from service account}
DEFAULT_SPREADSHEET_ID=<your-spreadsheet-id>
DATABASE_URL=postgresql://user:password@host:5432/db
CORS_ORIGINS=https://your-frontend.com,http://localhost:3000
DEBUG_ROUTES_ENABLED=false
VITE_IMG_JACOB_TOKEN=
VITE_IMG_JONATHAN_TOKEN=
VITE_IMG_ALEX_TOKEN=
VITE_IMG_JENNIFER_TOKEN=
```

⚠️ **Security**: Never commit `.env` to git. It's in `.gitignore`.

### 3. Test Locally

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Visit: http://localhost:8000/doc

### 4. Verify Data Parsing

Use debug endpoints to inspect sheet structure:

```bash
curl http://localhost:8000/debug/sheets/METAS/schema
curl http://localhost:8000/debug/sheets/BASE_VENDAS/schema
```

Check:
- Headers detected at correct row
- Empty rows/columns removed
- Month columns identified (if any)
- No parsing errors in logs

If errors, check:
- Spreadsheet ID correct?
- Service account has access?
- Sheet names match exactly (case-sensitive)?

### 5. Test Key Endpoints

```bash
# Goals (should return metas from METAS tab)
curl http://localhost:8000/goals

# Users (should return from dash_users table)
curl http://localhost:8000/users

# Statistics (current month + past months)
curl -X POST http://localhost:8000/statistics \
  -H "Content-Type: application/json" \
  -d '{"start_date": 0, "end_date": 9999999999999}'

# Finance (should return safe defaults until wiring complete)
curl http://localhost:8000/sales/finance

# Pre-sales (should return 5 channels)
curl http://localhost:8000/pre-sales/funnels
```

## Next Day (Testing & Deployment)

### 1. Unit Tests (Already Done)

```bash
python -m pytest tests/ -v
```

All 79 tests should pass.

### 2. Build Docker Image

```bash
docker build -t atlaz-dash-backend:latest .
```

Test image:

```bash
docker run -p 8000:8000 \
  -e GOOGLE_SHEETS_CREDENTIALS_JSON='...' \
  -e DEFAULT_SPREADSHEET_ID='...' \
  -e DATABASE_URL='...' \
  atlaz-dash-backend:latest
```

### 3. Deploy to Easypanel

Follow `DEPLOY.md`:

1. Create service in Easypanel
2. Set build path: `./Dockerfile`
3. Paste environment variables from `.env`
4. Set port mapping: 8000 → 8000
5. Deploy
6. Monitor logs

### 4. Verify Deployment

Test health endpoint:

```bash
curl https://<your-easypanel-domain>/health
```

Test Swagger:

```
https://<your-easypanel-domain>/doc
```

## After Deployment (Ongoing)

### 1. Monitor Logs

Check Easypanel dashboard for:
- Startup logs: "Application startup complete"
- Request logs: successful responses (200, 201)
- Errors: DataSourceError, timeout, validation failures

### 2. Set Up Monitoring (Optional)

Monitor endpoint: `GET /health` (returns `{"status": "ok"}`)

### 3. Phase 2 Implementation (Advanced)

The following endpoints return safe defaults (empty/zeroed):

- `GET /sales/finance` — reads BASE_VENDAS, returns empty structure
- `GET /pre-sales/funnels` — reads BASE_VENDAS, returns 5 channels zeroed

To implement full data parsing:

1. Use debug routes to inspect BASE_VENDAS structure:
   ```bash
   GET /debug/sheets/BASE_VENDAS/raw
   GET /debug/sheets/BASE_VENDAS/schema
   GET /debug/sheets/BASE_VENDAS/normalized
   ```

2. Update `app/services/finance_service.py`:
   - Parse blocks for financial data
   - Aggregate by product, channel, month
   - Calculate deltas, margins, percentages

3. Update `app/services/pre_sales_service.py`:
   - Parse blocks for funnel data
   - Group by channel (linkedin, instagram, etc.)
   - Extract funnel steps and KPIs

4. Add unit tests for new logic

5. Deploy (Easypanel auto-redeploys on git push if configured)

## Troubleshooting

### API returns empty/default data

Check in order:

1. Google Sheets API credentials valid?
   ```bash
   curl http://localhost:8000/debug/sheets/METAS/raw
   ```
   Should return matrix, not error.

2. Spreadsheet ID correct?
   Check `.env` value matches URL.

3. Service account has read access?
   Check spreadsheet sharing settings.

4. Sheet name correct?
   Check exact spelling: "METAS", "BASE_VENDAS" (case-sensitive).

### Database connection error

Check:

1. DATABASE_URL format: `postgresql://user:pass@host:5432/db`
2. Supabase instance running?
3. Network accessible from container?
4. User/password correct?

### n8n statistics timeout

Expected behavior — the API waits 10s for n8n response, then returns empty stats.

Check logs for: `WARNING: n8n_statistics_client: timeout`

Verify:
- N8N_STATISTICS_URL correct?
- n8n webhook active?
- Network accessible from container?

### Port conflict on Easypanel

If deployment fails due to port:
1. Check if port 8000 already in use
2. Use different port (8001, 8002, etc.)
3. Update port mapping in Easypanel

## Success Criteria

✅ API responds to all endpoints
✅ `/health` returns `{"status": "ok"}`
✅ `/doc` shows Swagger UI
✅ `/goals` returns data or safe defaults
✅ `/users` returns users or empty array
✅ `/statistics` returns data with both current+past months
✅ Logs show no persistent errors
✅ Response times < 1s per endpoint

## Need Help?

1. Check logs in Easypanel: **Service → Logs**
2. Use debug routes to inspect data: `/debug/sheets/{tab}/schema`
3. Review architecture: See `README.md` → **How It Works** section
4. Check specific service: See `README.md` → **Architecture** section

## Git History

All work committed to `main` branch:

```
c49b73d Add comprehensive README with setup, API reference, and architecture
a8a2455 Add Easypanel deployment guide
ae18921 Wire Phase 2 sales finance and pre-sales endpoints
8dcdc13 Wire historical statistics repository to actual Supabase tables
```

Pull latest to ensure all fixes are included.
