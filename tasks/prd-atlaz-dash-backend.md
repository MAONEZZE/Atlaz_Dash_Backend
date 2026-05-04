# PRD: Atlaz Dash Backend (FastAPI)

## 1. Introduction / Overview

FastAPI backend that powers the **Atlaz Dash** dashboard. Acts as a read-only adapter layer that ingests messy data from three sources (Google Sheets, Supabase Postgres, n8n external API), normalizes it, and serves stable, predictable JSON contracts to the frontend.

Hard constraint: backend is **read-only** against Google Sheets (scope `https://www.googleapis.com/auth/spreadsheets.readonly`). No write/update/delete/insert routes anywhere in the API.

> **Constraint absoluta:** A única ação permitida nas planilhas do Google Sheets é **extração de dados (leitura)**. Nenhum código, biblioteca, helper, script ou rota pode escrever, editar, atualizar, inserir, mesclar, formatar, renomear ou deletar dados/abas/células das planilhas. Qualquer tentativa de uso de método de escrita da Google Sheets API (ex.: `values.update`, `values.append`, `values.clear`, `batchUpdate`) é proibida e deve ser ativamente impedida na revisão de código.

**Phase 1 scope:** Visão Geral (overview) area. Pré-vendas and Vendas areas are scaffolded (routes/DTOs/mappers stubs returning safe empty contracts) but real data wiring lands in later phases.

### Inputs decided

- **Database:** Supabase (Postgres). Connect via `DATABASE_URL` (Supabase pooler connection string).
- **Spreadsheet ID:** `1NrKYW3BByJJ688ILwG20AvBuc-YggkwkOun34Ewjwck`.
- **Tabs:** `METAS`, `BASE_VENDAS`.
  - `METAS` → individual goals + team revenue goal.
  - `BASE_VENDAS` → all sales/financial raw data.
- **Auth:** none. CORS-only, allowlist via `CORS_ORIGINS`.
- **User aliasing:** `jonny` and `jonathan` map to the same person. Alias normalization required.
- **Bloco solto** `{bruto, liquido, parcelasAnt, totalLiquido, vendas}`: all financial data comes from `BASE_VENDAS`. Treat this block as part of the FIN_RESUMO derivation pipeline; not a separate top-level frontend key. Drop unless frontend explicitly asks for it.

---

## 2. Goals

- Serve a stable JSON contract per dashboard area; never expose raw sheet structure.
- Numeric fields are **always numbers** — never `null`, `NaN`, or `undefined`.
- External failure (Sheets / Supabase / n8n) never breaks frontend: degrade to safe-zeroed structures + internal warning log.
- Current-month statistics come from n8n; past months come from Supabase. Mixed-period requests consolidate both.
- Identity normalization: `jonny == jonathan`, etc.
- Phase 1: full working Visão Geral pipeline end-to-end. Other areas: scaffolded, return valid empty contracts.

---

## 3. User Stories

### US-001: Project bootstrap & config
**Description:** As a developer, I want a runnable FastAPI app with config, logging, and CORS so further work has a foundation.

**Acceptance Criteria:**
- [ ] `app/main.py` boots with `uvicorn`.
- [ ] `app/core/config.py` loads env via `pydantic-settings`.
- [ ] `app/core/logging.py` uses `loguru`.
- [ ] CORS middleware reads `CORS_ORIGINS` (comma-separated).
- [ ] `.env.example` committed with all variables from Part 16 of the source spec.
- [ ] Global exception handler returns JSON-stable error shape (never crashes frontend).
- [ ] `requirements.txt` (or `pyproject.toml`) lists deps from Part 15.
- [ ] Typecheck/lint passes.

### US-002: Health check endpoint
**Description:** As an ops user, I want `GET /health` to confirm the service is alive.

**Acceptance Criteria:**
- [ ] `GET /health` returns `{"status": "ok"}` with HTTP 200.
- [ ] No external dependency required for the response.

### US-003: Google Sheets read-only client
**Description:** As a developer, I want a Sheets client that only reads data, locked to the readonly scope.

**Acceptance Criteria:**
- [ ] `app/services/google_sheets_service.py` connects via service account credentials at `GOOGLE_APPLICATION_CREDENTIALS`.
- [ ] Scope hardcoded/asserted to `https://www.googleapis.com/auth/spreadsheets.readonly`.
- [ ] Functions: `read_tab(spreadsheet_id, tab_name) -> list[list]`, `read_tabs(spreadsheet_id, tab_names) -> dict[str, list[list]]`.
- [ ] No write/update/append/clear methods exposed or imported.
- [ ] Raises typed exception on auth/network failure; never silently mutates sheet.
- [ ] Default spreadsheet ID `1NrKYW3BByJJ688ILwG20AvBuc-YggkwkOun34Ewjwck` via `DEFAULT_SPREADSHEET_ID`.

### US-004: Sheet parser service
**Description:** As a developer, I want raw sheet matrices parsed into clean tabular blocks despite messy formatting.

**Acceptance Criteria:**
- [ ] `app/services/sheet_parser_service.py` removes empty rows and empty columns.
- [ ] Detects header row even when not row 0.
- [ ] Detects multiple data blocks within a single tab (mid-sheet titles split blocks).
- [ ] Detects month columns (`Jan`, `Fevereiro`, `mai/2026`, `2026-05`, etc.).
- [ ] Pivots horizontal month columns into vertical rows when needed.
- [ ] Preserves original `(row_idx, col_idx)` reference per parsed cell for debug.
- [ ] Unit tests cover: empty rows, empty cols, header at row 3, mid-sheet title, month columns horizontal-to-vertical.

### US-005: Normalization utilities
**Description:** As a developer, I want pure functions that normalize text, currency, dates, percentages, and numbers per Part 11 of the spec.

**Acceptance Criteria:**
- [ ] `app/utils/normalize_text.py`: trims, strips zero-width chars, collapses whitespace, normalizes accents for internal compare only.
- [ ] `app/utils/normalize_currency.py`: `"R$ 1.500,00" | "1.500,00" | "1500,00" | "1500" | 1500 → 1500.00`. Returns `0.0` on invalid + warning.
- [ ] `app/utils/normalize_date.py`: accepts ms timestamp, `dd/mm/yyyy`, `yyyy-mm-dd`, `mai/2026`, `maio 2026`. Returns `datetime` or `None`.
- [ ] `app/utils/normalize_percentage.py`: `"10%" | "10,5%" | 0.10 | 10 → standardized float`.
- [ ] `app/utils/normalize_number.py`: empty/invalid → `0`, logs warning. Never returns `NaN`/`None` for numeric pipeline outputs.
- [ ] Unit tests cover each format example listed.

### US-006: Field map + alias resolution
**Description:** As a developer, I want a single source of truth for sheet field aliases and person-name aliases.

**Acceptance Criteria:**
- [ ] `app/core/field_maps.py` contains `FIELD_MAP` from Part 10 of the spec.
- [ ] Same file contains `NAME_ALIASES` map: `{"jonny": "Jonathan"}` (extensible).
- [ ] Helper `resolve_field(label: str) -> str | None` returns canonical key.
- [ ] Helper `resolve_name(name: str) -> str` returns canonical display name (case-insensitive, accent-insensitive match; output keeps proper-case canonical form).
- [ ] Unit tests: `jonny → Jonathan`, `JONNY → Jonathan`, `Jônny → Jonathan`, unknown → input unchanged.

### US-007: n8n statistics client
**Description:** As a developer, I want an HTTP client for the n8n current-month stats endpoint that never propagates failure to the frontend.

**Acceptance Criteria:**
- [ ] `app/services/n8n_statistics_client.py` calls `N8N_STATISTICS_URL` with `httpx`.
- [ ] Timeout from `N8N_STATISTICS_TIMEOUT_SECONDS` (default 10s).
- [ ] On timeout / network error / non-2xx / invalid JSON / shape mismatch: returns empty `{"SDR": [], "CLOSER": []}`, logs `warning`.
- [ ] Validates response shape (top keys `SDR`, `CLOSER`; lists of dicts).
- [ ] Returns raw n8n shape — no field renaming here.
- [ ] Unit tests with mocked httpx: success, 500, timeout, malformed JSON, missing keys.

### US-008: Period detection service
**Description:** As a developer, I want a helper that decides per request whether n8n / DB / both should be queried, using America/Sao_Paulo timezone.

**Acceptance Criteria:**
- [ ] Helper `classify_period(start_ms, end_ms) -> {"current": bool, "past": bool, "current_range": (..), "past_range": (..)}`.
- [ ] Uses `America/Sao_Paulo` for "current month" boundaries.
- [ ] If range overlaps current month → `current=True`. If range covers any day before current month start → `past=True`.
- [ ] Mixed range returns both flags + correctly split sub-ranges.
- [ ] Unit tests: range fully in current month, fully past, straddling boundary, missing dates (defaults).

### US-009: Historical statistics repository (Supabase)
**Description:** As a developer, I want a repository that queries Supabase Postgres for past-month statistics with the spec's filter set.

**Acceptance Criteria:**
- [ ] `app/repositories/historical_statistics_repository.py` connects via `DATABASE_URL` (Supabase pooler).
- [ ] Function accepts filters: `start_date`, `end_date` (ms), `channel`, `responsible`, `product`, `stage`, `status`, `revenue_type`, `ticket_range`, `activity`.
- [ ] Empty filter values are ignored (no false positives on `""` / `None`).
- [ ] Text comparisons use normalized form (case + accent insensitive).
- [ ] Returns rows already aggregated per Closer / SDR (or grouped per service layer).
- [ ] Returns `[]` (not error) when no rows match.
- [ ] Connection errors → logged warning + empty result; never bubble to HTTP.
- [ ] Schema assumption documented: backend expects pre-existing tables (Supabase). Migration design lives in a follow-up task — initial implementation may stub queries against agreed table names.
- [ ] **Open question:** confirm exact Supabase table names + columns with stakeholder before finalizing queries.

### US-010: Statistics service (consolidation)
**Description:** As a developer, I want the service that picks current-vs-past sources, consolidates, and prepares data for the DTO mapper.

**Acceptance Criteria:**
- [ ] `app/services/statistics_service.py` accepts the filter schema.
- [ ] Calls `classify_period`; routes current to n8n client, past to historical repo.
- [ ] Consolidates by canonical name (uses `resolve_name`) — sums per-field across sources.
- [ ] Returns internal normalized model (not DTO) keyed by Closer / SDR.
- [ ] Empty result → returns valid empty internal model (no crash).
- [ ] Unit tests: current-only, past-only, mixed, n8n failure (returns past-only + warning), repo failure (returns current-only + warning).

### US-011: Statistics DTOs + mapper
**Description:** As a frontend dev, I want statistics returned in the exact contract from Part 1 of the spec.

**Acceptance Criteria:**
- [ ] `app/dtos/n8n_statistics_dto.py`: `N8nSdrStatisticDTO`, `N8nCloserStatisticDTO` with raw n8n field names.
- [ ] `app/dtos/statistics_dto.py`: `FrontendCloserStatisticDTO`, `FrontendSdrStatisticDTO`, `StatisticResponseDTO`.
- [ ] Frontend DTOs use **exact** field names with `\n` literals: `"Ligações\nRealizadas"`, `"Conexões\nEnviadas"`, `"Follow-ups"`, etc. (preserved on JSON serialization).
- [ ] All numeric fields default to `0` (Pydantic default), never optional/null.
- [ ] `app/mappers/n8n_statistics_mapper.py` converts n8n raw → internal normalized model.
- [ ] `app/mappers/statistics_mapper.py` converts internal model → final DTO.
- [ ] Unit tests: missing field in source → `0` in DTO; n8n empty → DTO with empty `CLOSER` and `SDR` arrays.

### US-012: Statistics route (`/statistics`)
**Description:** As a frontend dev, I want a route that accepts the filter payload and returns the final consolidated statistics contract.

**Acceptance Criteria:**
- [ ] `app/api/routes/statistics.py` exposes `POST /statistics` (or `GET` with query params — pick one and document).
- [ ] Request validated by `app/schemas/filters_schema.py` (mirrors filter set in Part 1).
- [ ] Response shape matches Part 1 final contract: `{"data": [{"CLOSER": [...], "SDR": [...]}]}`.
- [ ] Empty data → `{"data": [{"CLOSER": [], "SDR": []}]}`. Never 500 on data shortage.
- [ ] Integration test (with mocked n8n + repo) covers happy path + both-empty path.

### US-013: Goals service + DTOs + route (METAS tab)
**Description:** As a frontend dev, I want individual goals fetched from the `METAS` sheet tab in the contract from Part 2.

**Acceptance Criteria:**
- [ ] `app/repositories/goals_repository.py` reads `METAS` tab via Sheets service.
- [ ] `app/services/goals_service.py` parses + normalizes per-user goal rows.
- [ ] `app/dtos/goals_dto.py`: `SalesGoalsDTO` with fields `Nome`, `Cargo` (`"Closer" | "SDR"`), `Meta_Mensal`, `Meta_Numeros`, `Meta_Leads`, `Meta_Ligacoes`, `Meta_Reunioes`, `Meta_Indicacoes` (all numeric default `0`).
- [ ] `app/mappers/goals_mapper.py` → DTO.
- [ ] Route `GET /goals` returns `{"data": [SalesGoalsDTO, ...]}`.
- [ ] Sheet read failure → `{"data": []}` + warning. Never 500.

### US-014: Team realized totals route
**Description:** As a frontend dev, I want team realized totals in the contract from Part 3.

**Acceptance Criteria:**
- [ ] `app/services/team_service.py` aggregates current realized totals (source: same statistics pipeline, summed across people).
- [ ] `app/dtos/goals_dto.py` adds `TeamGoalsDTO` with `numeros_captados`, `ligacoes_agendadas`, `reunioes_agendadas`, `indicacoes` (numeric default `0`).
- [ ] Route `GET /team/realized` returns `{"data": [TeamGoalsDTO]}`.
- [ ] Empty result → `{"data": [{"numeros_captados": 0, ...}]}`.

### US-015: Users service + route
**Description:** As a frontend dev, I want user listing with id, name, role (lowercase), and image URL per Part 4.

**Acceptance Criteria:**
- [ ] `app/services/user_service.py` derives users from `METAS` (canonical names + roles).
- [ ] Applies `resolve_name` so `jonny → Jonathan` (no duplicate user).
- [ ] `app/dtos/users_dto.py`: `UserInfoDTO` with `id` (slug of canonical name), `nome`, `cargo` (`"closer" | "sdr"` lowercase), `imagem_url`.
- [ ] Image URL composed from per-user env tokens `VITE_IMG_<NAME>_TOKEN`. Missing token → `imagem_url = ""`.
- [ ] Tokens never logged.
- [ ] Route `GET /users` returns `{"data": [UserInfoDTO, ...]}`.

### US-016: Per-user statistics route
**Description:** As a frontend dev, I want stats for a single user via userId.

**Acceptance Criteria:**
- [ ] Route `GET /users/{user_id}/statistics` accepts canonical user id.
- [ ] Reuses statistics service, filters to that user (via `resolve_name`).
- [ ] Unknown user → `200` with empty consistent payload + warning logged. No 5xx.
- [ ] DTO `UserStatisticsDTO` defined in `app/dtos/users_dto.py` with deterministic shape (decided at impl time, documented in code).

### US-017: Sales finance scaffolding (Phase 2 placeholder)
**Description:** As a developer, I want sales-finance routes/DTOs/mappers scaffolded so the frontend can integrate against stable empty contracts before real data is wired.

**Acceptance Criteria:**
- [ ] `app/dtos/sales_values_dto.py` defines all DTOs from Part 6: `FinancialSummaryDTO`, `FinancialMonthDTO`, `ProductRevenueDTO`, `ChannelRevenueDTO`, `FinancialBreakdownDTO`, `MonthlyFinancialTableDTO`, `MonthlyFinancialTableRowDTO`.
- [ ] All numeric fields default to `0`, arrays default to `[]`, strings to `""`. `cor` defaults to a neutral hex from `app/utils/colors.py`.
- [ ] Route `GET /sales/finance` returns the full Part 6 envelope with safe defaults (12 months in `MESES_FIN`, `mesAtualIdx` derived from America/Sao_Paulo current month, `linhas` empty).
- [ ] Source noted in code comments: data lives in `BASE_VENDAS` tab; wiring deferred to a later phase. **Out-of-scope for Phase 1.**

### US-018: Pre-sales scaffolding (Phase 2 placeholder)
**Description:** As a developer, I want pre-sales funnel routes/DTOs scaffolded with safe defaults for all five required channels.

**Acceptance Criteria:**
- [ ] `app/dtos/pre_sales_dto.py`: `PreSalesFunnelDTO`, `ChannelFunnelDTO`, `FunnelStepDTO`, `FunnelKpiDTO`, `FunnelAuxDTO`, `FunnelAuxBlockDTO`.
- [ ] `fmt` literal-restricted to `"num" | "pct" | "dec" | "h" | "dias"`.
- [ ] Route `GET /pre-sales/funnels` always returns all five channels (`linkedin`, `instagram`, `indicacao`, `whatsapp`, `outros`) — zero-valued when no data.
- [ ] Default colors come from `app/utils/colors.py`. **Out-of-scope for Phase 1** — wiring deferred.

### US-019: Debug routes
**Description:** As a developer, I want debug-only routes per Part 12 to inspect raw + normalized sheet data.

**Acceptance Criteria:**
- [ ] `app/api/routes/sheets_debug.py` mounted under `/debug` prefix.
- [ ] `GET /debug/sheets/{tab}/raw` → raw matrix.
- [ ] `GET /debug/sheets/{tab}/schema` → detected headers, empty rows/cols, financial-field candidates, date candidates, month columns, warnings.
- [ ] `GET /debug/sheets/{tab}/normalized` → post-normalization rows.
- [ ] Routes gated by `DEBUG_ROUTES_ENABLED` env (default `false` in production).
- [ ] Documented as **not for frontend** in route docstring.

### US-020: Global error handling + warning log channel
**Description:** As a frontend dev, I never want a 5xx from this backend on a data issue.

**Acceptance Criteria:**
- [ ] FastAPI exception handler converts unexpected exceptions to JSON `{"error": "...", "data": <empty-shape>}` with HTTP 200 on data-source failures (per "never break the frontend").
- [ ] Validation errors (`422`) remain `422` (frontend bug, not data bug).
- [ ] All source-side failures logged at `WARNING` with structured context (source name, filters, exception).
- [ ] No secret (Google creds path content, image tokens, DB password) ever appears in log output.

---

## 4. Functional Requirements

- FR-1: Sheets access uses **only** scope `https://www.googleapis.com/auth/spreadsheets.readonly`. No write APIs imported anywhere.
- FR-1.1: **Única ação permitida nas planilhas: extração de dados (leitura).** Forbidden: `values.update`, `values.append`, `values.clear`, `values.batchUpdate`, `spreadsheets.batchUpdate`, any cell/format/sheet-structure mutation. Code review must reject any PR that imports or calls these methods.
- FR-2: Spreadsheet ID configurable; default = `1NrKYW3BByJJ688ILwG20AvBuc-YggkwkOun34Ewjwck`.
- FR-3: Backend reads two tabs: `METAS` (goals + users) and `BASE_VENDAS` (sales/financial).
- FR-4: Current-month statistics fetched from `N8N_STATISTICS_URL`; past-month from Supabase historical repository; mixed periods consolidated.
- FR-5: Current month determined by `America/Sao_Paulo` timezone using server clock.
- FR-6: All filters acumulative; empty values ignored; text compares accent/case-insensitive.
- FR-7: Statistics response uses literal `\n` characters in field names (e.g., `"Ligações\nRealizadas"`).
- FR-8: Numeric fields in any DTO default to `0`. Arrays default to `[]`. Strings default to `""`. No `null` / `NaN` / `undefined` ever in numeric outputs.
- FR-9: User aliases resolved via `NAME_ALIASES` (e.g. `jonny ↔ Jonathan`). All grouping/aggregation uses canonical name.
- FR-10: Image tokens read from `VITE_IMG_<NAME>_TOKEN`. Missing token → empty `imagem_url`. Tokens never logged.
- FR-11: All external sources (Sheets, n8n, Supabase) wrapped with timeout + try/except; failure → safe empty contract + WARNING log.
- FR-12: CORS origins come from `CORS_ORIGINS` (comma-separated).
- FR-13: No write/update/delete/insert/PATCH/PUT/POST routes that mutate any source. POST allowed only for filter-bearing read endpoints.
- FR-14: Final responses always pass through Pydantic DTOs — internal models never serialized directly.
- FR-15: Months abbreviated: `Jan, Fev, Mar, Abr, Mai, Jun, Jul, Ago, Set, Out, Nov, Dez`.
- FR-16: Currency parser handles `R$ 1.500,00`, `1.500,00`, `1500,00`, `1500`, `1500` → `1500.00`. Invalid → `0.0` + warning.
- FR-17: Date parser handles ms timestamp, `dd/mm/yyyy`, `yyyy-mm-dd`, `mai/2026`, `maio 2026`.
- FR-18: Pre-sales `fmt` restricted to `num | pct | dec | h | dias`.
- FR-19: Pre-sales response always includes all five channels (`linkedin`, `instagram`, `indicacao`, `whatsapp`, `outros`), zeroed if no data.
- FR-20: Sales-finance summary fields conform to Part 6 contract; bloco solto `{bruto, liquido, parcelasAnt, totalLiquido, vendas}` is **not** added as a separate frontend key (data merged into FIN_RESUMO derivation; revisit if frontend confirms otherwise).

---

## 5. Non-Goals (Out of Scope)

- **No write operations** of any kind to Google Sheets.
- **No auth** layer (no JWT / API keys / OAuth) — CORS allowlist only. Add later if needed.
- **No Phase-1 real data** for Pré-vendas and Vendas — scaffolded routes return safe empty contracts. Data wiring is a later phase.
- No Supabase schema design / migrations as part of this PRD — backend assumes tables exist or stubs queries until schema is confirmed.
- No caching layer (Redis/in-memory). Add only if perf demands later.
- No background jobs, schedulers, or webhooks.
- No frontend code, UI, or visual design.
- No Docker/compose/k8s manifests in this PRD (can be added separately).
- No tests beyond unit + a few integration smoke tests on the statistics route.

---

## 6. Technical Considerations

### Architecture (per Part 9 of source spec)

```
app/
  main.py
  api/routes/        # statistics, goals, users, sales_values, pre_sales, sheets_debug
  services/          # google_sheets, sheet_parser, normalization, statistics, n8n_statistics_client, goals, team, user, sales_finance, pre_sales
  repositories/      # sheets, historical_statistics, goals, users, sales_finance, pre_sales
  schemas/           # pydantic request schemas
  dtos/              # pydantic response DTOs
  mappers/           # internal -> DTO conversion
  utils/             # normalize_*, detect_*, remove_*, colors
  core/              # config, field_maps, logging, exceptions
```

### Stack

- Python 3.11+
- `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`
- `google-api-python-client`, `google-auth`
- `httpx` for n8n client (async)
- `sqlalchemy` + `asyncpg` (Supabase Postgres)
- `loguru` logging
- `python-dateutil`, `pandas` for parsing helpers

### Integration points

- **Supabase:** Postgres via pooled `DATABASE_URL`. Table names + columns require confirmation (open question).
- **Google Sheets:** service-account JSON at `GOOGLE_APPLICATION_CREDENTIALS`. Service account must have read access shared on the spreadsheet.
- **n8n:** `https://n8n.learningbrands.cloud/webhook/statistic`. Timeout 10s default.

### Security

- All secrets via env. `.env` git-ignored, `.env.example` committed.
- Image tokens redacted in logs.
- No mutating routes anywhere.
- CORS strict allowlist.
- Debug routes off by default in prod.

### Performance

- Sheets reads cached per-request (memoize within request lifecycle) to avoid duplicate fetches between services.
- n8n client uses async httpx with explicit timeout; never blocks request indefinitely.

---

## 7. Success Metrics

- Frontend never receives `null`/`NaN`/`undefined` in any numeric field. Verified by integration tests asserting type equality on every numeric DTO field.
- Visão Geral statistics route returns valid contract under all four scenarios: current-only, past-only, mixed, all-sources-down.
- 100% of debug route output redacted of secrets.
- Sheets API audit log shows zero write operations (only `spreadsheets.values.get` / `batchGet`).
- Phase 1 done = Visão Geral end-to-end runs against real data; Pré-vendas + Vendas routes return scaffolded contracts with safe defaults.

---

## 8. Open Questions

1. **Supabase schema** — exact table + column names for historical statistics? Need confirmation before wiring `historical_statistics_repository`. Until then, the repo stubs to return `[]` and logs intent.
2. **`POST` vs `GET`** for `/statistics` — payload-bearing filters point to `POST`; confirm frontend preference.
3. **Bloco solto** `{bruto, liquido, parcelasAnt, totalLiquido, vendas}` — confirmed to be derived from `BASE_VENDAS`. Final destination key in frontend payload still ambiguous; current decision = merge into `FIN_RESUMO` (drop standalone). Revisit if frontend explicitly references it.
4. **Default image** when `imagem_url` missing — empty string for now; placeholder URL TBD.
5. **User id slug rule** — slugify canonical name (`jonathan`, `jacob`, `alex`, `jennifer`)? Confirm exact format with frontend.
6. **Goal row layout in `METAS`** — header position + per-row vs per-column structure not yet inspected. Implementation needs a debug pass on the live tab before final parser logic.
7. **`BASE_VENDAS` block layout** — same: needs live inspection before Phase 2 wiring.
