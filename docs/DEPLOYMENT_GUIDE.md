# 🚀 ZAA Deployment Guide

## Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase project with the Data API enabled
- Meta Developer Account (for WhatsApp)
- MTN MoMo Developer Account (for payments)

---

## PART 1: Backend Deployment (FastAPI)

### Step 1: Install Dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
```

### Step 2: Set Environment Variables
Copy `.env.example` to `.env` and fill in:
```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SECRET_KEY=your_supabase_secret_key
CORS_ORIGINS=https://your-frontend.example.com
WHATSAPP_TOKEN=your_whatsapp_cloud_api_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=zaa_verify_token_2024
GROQ_API_KEY=your_groq_api_key
HF_API_TOKEN=your_huggingface_token
MOMO_API_USER=your_momo_user
MOMO_API_KEY=your_momo_key
MOMO_SUBSCRIPTION_KEY=your_momo_subscription_key
```

### Step 3: Initialize Supabase
Apply `database/schema.sql` to the connected Supabase project using the Supabase SQL migration workflow. Confirm the tables are exposed through the Data API and that RLS is enabled before sending production traffic.

### Step 4: Run Locally
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Deploy to Render (Free)
1. Push code to GitHub
2. Connect Render to your repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render dashboard
6. Deploy!

### Step 6: Configure WhatsApp Webhook
1. Go to developers.facebook.com
2. Your app → WhatsApp → Configuration
3. Webhook URL: `https://your-render-url.onrender.com/api/v1/whatsapp/webhook`
4. Verify token: `zaa_verify_token_2024`
5. Subscribe to `messages` events

---

## PART 2: Frontend Deployment (Next.js)

### Step 1: Install Dependencies
```bash
cd frontend
npm install
```

### Step 2: Set API URL
Create `.env.local` file:
```
NEXT_PUBLIC_API_URL=https://your-render-url.onrender.com/api/v1/marketplace
```

### Step 3: Build & Deploy to Vercel (Free)
```bash
npm run build
vercel --prod
```

Or connect your GitHub repo to Vercel for auto-deployment.

---

## PART 3: WhatsApp Business Setup

### 1. Create Meta Developer Account
- https://developers.facebook.com

### 2. Create Business App
- App Type: Business
- Add Product: WhatsApp

### 3. Get Test Number
- Meta provides a free test phone number
- You can message it from up to 5 phone numbers

### 4. Get Permanent Token
- Go to System Users in Business Settings
- Generate token with `whatsapp_business_messaging` permission

### 5. Verify Business (for production)
- Submit business documents
- Wait 1-2 weeks for approval
- Then you can message any WhatsApp user

---

## PART 4: MTN MoMo Setup

### 1. Register Developer Account
- https://momodeveloper.mtn.com

### 2. Create API User & Key
- Sandbox environment for testing
- Production requires business registration

### 3. Get Subscription Key
- Found in your MTN developer profile

---

## PART 5: First Test

### Test 1: Health Check
```bash
curl https://your-render-url.onrender.com/health
```
Should return: `{"status": "healthy"}`

### Test 2: WhatsApp Webhook
Send a message to your test number. Check server logs for incoming webhook.

### Test 3: Dashboard
Open `https://your-vercel-url.vercel.app` and verify listings load.

### Test 4: Place a Bid
1. Create a listing via WhatsApp
2. Open dashboard → should appear
3. Click "Place Bid"
4. Check farmer's WhatsApp for notification

---

## Architecture Summary

```
Farmer (WhatsApp) → Meta Servers → Your Render Backend → PostgreSQL (Supabase)
                                           ↓
Buyer Dashboard (Vercel) ← REST API ← Your Render Backend
```

**Unified Directory Structure:**
```
zaa_complete/
├── backend/                 # FastAPI application
│   ├── main.py             # Application entry point
│   ├── database.py         # Database connection
│   ├── services/           # Business logic (AI, marketplace, payments)
│   └── routers/            # API routes (whatsapp, marketplace)
├── frontend/               # Next.js buyer dashboard
│   └── app/                # Next.js app directory
├── database/               # Database schema
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── .env.example           # Environment variables template
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| WhatsApp webhook not receiving | Check verify token matches. Ensure HTTPS URL. |
| Supabase Data API failed | Verify SUPABASE_URL and the server-only SUPABASE_SECRET_KEY. Confirm tables are exposed through the Data API and RLS policies match the caller. |
| AI responses slow | Groq free tier = 20 req/min. Upgrade or cache responses. |
| MoMo payments failing | Use sandbox for testing. Verify subscription key. |
| CORS errors on dashboard | Check CORS middleware in main.py allows your Vercel domain. |
| Marketplace router errors | Ensure all service imports use correct paths (database.py vs services.database) |

---

## Development vs Production URLs

### Development
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Database: Supabase Data API

### Production
- Backend: `https://your-app.onrender.com`
- Frontend: `https://your-app.vercel.app`
- Database: Supabase Data API via `SUPABASE_URL` and `SUPABASE_SECRET_KEY`

---

## Next Steps After Deployment

1. **Week 1:** Get 10 test farmers in Tamale using the Price Bot
2. **Week 2:** Collect 50 shea butter photos for AI training
3. **Week 3:** Complete first real transaction (manual escrow)
4. **Week 4:** Apply for GIZ/USAID funding with transaction data
5. **Month 2:** Scale to 5 districts, add more commodities

---

## Support

For questions about the code, architecture, or strategy, refer to:
- `docs/USER_MANUAL.md` - Complete user guide for farmers and buyers
- `docs/STRATEGY_LANGUAGE_CONSTRAINTS_ADOPTION.md` - Business strategy
- `README.md` - Project overview and setup
- This deployment guide

**Built for Ghana. Built by Ghanaians. For Africa.** 🇬🇭
