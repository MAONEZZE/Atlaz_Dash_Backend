# Atlaz Dash Backend

FastAPI backend for Atlaz Dashboard. Read-only adapter layer for Google Sheets, Supabase, and n8n APIs.

## Features

- **Read-only Google Sheets integration** (strict readonly scope)
- **Historical data from Supabase** (dash_metricas_prospeccao, dash_users tables)
- **Real-time statistics from n8n** (current month data)
- **Smart period detection** (routes current month to n8n, past months to Supabase)
- **Messy data handling** (merged cells, month columns, mixed layouts)
- **Data normalization** (currency, dates, numbers, text)
- **Safe fallbacks** (no data = zeroed defaults, external API errors = graceful)
- **Debug routes** (inspect raw/schema/normalized sheet data)
- **Type-safe DTOs** (Pydantic validation)
- **Swagger + ReDoc** (full API documentation at `/doc`)

## Quick Start

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env from template
cp .env.example .env

# Edit .env with your values
# - GOOGLE_SHEETS_CREDENTIALS_JSON
# - DEFAULT_SPREADSHEET_ID
# - DATABASE_URL
# - CORS_ORIGINS
nano .env

# Run server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Visit http://localhost:8000/doc for API docs
```

### Docker

```bash
# Build
docker build -t atlaz-dash-backend .

# Run
docker run -p 8000:8000 \
  -e GOOGLE_SHEETS_CREDENTIALS_JSON='...' \
  -e DEFAULT_SPREADSHEET_ID='...' \
  -e DATABASE_URL='...' \
  atlaz-dash-backend
```

## Environment Variables

See `.env.example` for complete list. Required:

- `GOOGLE_SHEETS_CREDENTIALS_JSON` — Service account JSON (raw, not file path)
- `DEFAULT_SPREADSHEET_ID` — Your spreadsheet ID
- `DATABASE_URL` — Supabase postgres://... connection string
- `CORS_ORIGINS` — Comma-separated frontend URLs

## API Endpoints

### Statistics (Visão Geral)

```bash
POST /statistics
```

Body:
```json
{
  "start_date": 1234567890000,
  "end_date": 1234567890000,
  "responsible": "name (optional)"
}
```

Returns: `{data: [{CLOSER: [...], SDR: [...]}]}`

- Current month data from n8n API
- Past months data from Supabase
- Automatically consolidated

### Goals (Metas)

```bash
GET /goals
```

Returns: `{data: [{Nome, Cargo, Meta_Mensal, Meta_Numeros, ...}]}`

### Users (Usuários)

```bash
GET /users
GET /users/{user_id}/statistics
GET /team/realized
```

Returns user list, individual stats, and team totals.

### Sales Finance (Vendas)

```bash
GET /sales/finance
```

Returns: `{FIN_RESUMO, MESES_FIN, PRODUTOS, RECEITA_POR_CANAL, FIN_BREAKDOWN, TABELA_FIN_MENSAL}`

Reads from BASE_VENDAS tab.

### Pre-Sales (Pré-Vendas)

```bash
GET /pre-sales/funnels
```

Returns: `{FUNIS_POR_CANAL: {linkedin, instagram, indicacao, whatsapp, outros}}`

All 5 channels always present; zeroed when no data.

### Debug Routes

Gated by `DEBUG_ROUTES_ENABLED=true`

```bash
GET /debug/sheets/{tab}/raw        # Raw matrix
GET /debug/sheets/{tab}/schema     # Detected structure
GET /debug/sheets/{tab}/normalized # Parsed + normalized
```

## Testing

```bash
python -m pytest tests/ -v
```

79 tests covering:
- Data normalization (currency, dates, numbers)
- Field mapping (28+ aliases)
- Sheet parsing (headers, empty rows, month columns)
- Statistics DTOs and mappers

## How It Works

### Data Flow: Statistics

```
POST /statistics
  → period_service.classify_period(start, end)
    ├─ current month → n8n_statistics_client.fetch_current_month_statistics()
    └─ past months → historical_statistics_repository.fetch_historical_statistics()
  → statistics_service.consolidate() + normalize()
  → StatisticsResponseDTO
```

### Data Flow: Goals

```
GET /goals
  → read_tab(sheet, "METAS")
  → parse_tab(matrix) — detect headers, month columns, normalize cells
  → extract_goals() — group by user
  → GoalsResponseDTO
```

### Data Flow: Users

```
GET /users
  → SELECT * FROM dash_users
  → map to UserInfoDTO (compose image_url from VITE_IMG_*_TOKEN)
  → UsersResponseDTO
```

## Deployment

See `DEPLOY.md` for Easypanel-specific instructions.

Quick summary:
1. Prepare `.env` file with all variables
2. Build Docker image
3. Deploy to Easypanel
4. Set port to 8000
5. Test health endpoint

## Data Sources

| Data | Source | Access |
|------|--------|--------|
| Current month statistics | n8n webhook API | Read-only |
| Historical statistics | Supabase postgres | Read-only |
| Goals/Metas | Google Sheets (METAS tab) | Read-only |
| Users | Supabase (dash_users) | Read-only |
| Finance | Google Sheets (BASE_VENDAS tab) | Read-only |
| Pre-sales | Google Sheets (BASE_VENDAS tab) | Read-only |

## Guarantee: Never Writes, Edits, or Deletes

✅ Read-only Google Sheets scope: `spreadsheets.readonly`
✅ No write operations on Supabase tables
✅ No modifications to n8n webhook data
✅ Safe defaults on errors (no data = zeroed fields)

## Architecture

```
app/
├── main.py                    # FastAPI app, CORS, exception handlers, routes
├── core/
│   ├── config.py             # Pydantic Settings from .env
│   ├── field_maps.py         # 28+ field aliases (jonny → Jonathan)
│   └── exceptions.py         # DataSourceError, handlers
├── services/
│   ├── google_sheets_service.py      # read_tab(), read_tabs()
│   ├── sheet_parser_service.py       # parse_tab(), detect structure
│   ├── period_service.py             # classify_period(), timezone-aware
│   ├── statistics_service.py         # consolidate current+past
│   ├── n8n_statistics_client.py      # fetch_current_month_statistics()
│   ├── finance_service.py            # Phase 2: read BASE_VENDAS
│   └── pre_sales_service.py          # Phase 2: read BASE_VENDAS
├── repositories/
│   └── historical_statistics_repository.py  # Query dash_metricas_prospeccao
├── dtos/
│   ├── statistics_dto.py
│   ├── goals_dto.py
│   ├── users_dto.py
│   ├── sales_values_dto.py
│   └── pre_sales_dto.py
├── utils/
│   ├── normalize_currency.py
│   ├── normalize_date.py
│   ├── normalize_number.py
│   └── normalize_text.py
└── api/routes/
    ├── health.py
    ├── statistics.py
    ├── goals.py
    ├── users.py
    ├── sales_values.py
    ├── pre_sales.py
    └── sheets_debug.py
```

## Known Limitations (Phase 2)

- Finance data (GET /sales/finance) returns safe defaults
- Pre-sales data (GET /pre-sales/funnels) returns 5 channels, all zeroed
- Full parsing logic for BASE_VENDAS deferred (awaits structure validation with real data)

## Logs

Access via Easypanel dashboard or container logs. Example:

```
INFO:     Application startup complete
INFO:     GET /statistics - 200 OK
WARNING:  n8n_statistics_client: timeout | retry_count=3
ERROR:    DataSourceError: failed to read METAS tab
```

## Support

- **Debug Routes**: Use `/debug/sheets/{tab}/schema` to inspect data structure
- **Logs**: Check application logs for errors and warnings
- **Swagger**: Visit `/doc` for interactive API testing
