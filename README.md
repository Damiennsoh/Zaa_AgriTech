# ZAA — Voice-First Agricultural Exchange

ZAA connects farmers and buyers across Northern Ghana through WhatsApp and a buyer web dashboard. Farmers can ask for market prices, create produce listings, share photos or voice notes, receive notifications, and negotiate with buyers without installing a new app.

## Product surfaces

- **Farmer experience:** WhatsApp Cloud API, with support for Dagbani, Twi, Gonja, Hausa, and English workflows.
- **Buyer experience:** Next.js dashboard for browsing listings, checking prices, placing bids, and reviewing marketplace analytics.
- **Backend:** FastAPI service that handles WhatsApp webhooks, marketplace APIs, AI services, notifications, and MTN MoMo integration.
- **Data:** Supabase PostgreSQL accessed by the backend through the Supabase Data API with RLS enabled.

## Architecture

```text
WhatsApp Business API ─┐
                       ├─ FastAPI backend ── Supabase Data API
Buyer dashboard ───────┘          ├────────── AI providers
                                  └────────── MTN MoMo
```

## Repository layout

```text
backend/                 FastAPI application
  main.py                Application entry point and health endpoint
  database.py            Supabase Data API adapter
  routers/               WhatsApp and marketplace routes
  services/              AI, listings, bids, payments, groups, and jobs
database/schema.sql      Canonical schema reference
docs/                    Deployment and product documentation
frontend/                Next.js buyer dashboard
requirements.txt         Backend dependencies
.env.example             Environment variable template
```

## Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- A Supabase project with the Data API enabled
- Meta Developer account with WhatsApp Cloud API access
- MTN MoMo developer account for payment flows

## Local development

### 1. Configure the backend

```bash
cp .env.example .env
pip install -r requirements.txt
```

Set at minimum:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SECRET_KEY=your_server_only_supabase_secret_key
CORS_ORIGINS=http://localhost:3000
```

Never expose `SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_ROLE_KEY` to the browser. Apply `database/schema.sql` through the Supabase migration workflow before exercising data-backed routes.

### 2. Start the API

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API root: `http://localhost:8000/`
- Health check: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`

### 3. Start the dashboard

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` to the backend marketplace API URL when required by the dashboard.

## Production deployment

The supported deployment split is:

- **FastAPI:** Render, Railway, or another Python host running `uvicorn main:app --host 0.0.0.0 --port $PORT` from `backend/`.
- **Next.js:** Vercel using the `frontend/` directory as the project root and `npm run build` as the build command.
- **Database:** Supabase Data API, with production secrets configured in the backend host and public keys only in the frontend when needed.

Use [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) for environment variables, webhook setup, Supabase initialization, health checks, and release validation.

## Security notes

- Keep Supabase server credentials server-side.
- Keep RLS enabled on exposed Supabase tables.
- Restrict `CORS_ORIGINS` to the deployed dashboard origin; do not use `*` with credentials.
- Configure WhatsApp and payment secrets only in the deployment provider's secret manager.
- Validate webhook signatures and payment callbacks before enabling production transactions.

## Current status and next steps

The root backend is wired to Supabase and the marketplace schema has been provisioned. Before public launch, connect the production WhatsApp number, configure custom email/authentication if the dashboard requires accounts, validate MTN MoMo in sandbox, add automated API tests, and perform an end-to-end transaction rehearsal.

## License

MIT. Built for Ghana and the wider African agricultural ecosystem.
