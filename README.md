# 🌾 ZAA - The Voice-First AI Agricultural Exchange
## For Northern Ghana | Built by Ghanaians, For Africans

### What is ZAA?
ZAA (meaning "tomorrow" in Dagbani) is an AI-powered agricultural trading layer that lives inside WhatsApp. 
No apps to download. No smartphones required. No literacy needed.

A farmer in Walewale sends a voice note in Dagbani. ZAA understands, grades their produce from a photo, 
finds them a buyer, and ensures payment via MTN MoMo.

### How "Lives in WhatsApp" Actually Works
ZAA is NOT an app inside WhatsApp. There is no "ZAA button" you tap inside your WhatsApp. Instead, ZAA is a backend service that communicates with users through WhatsApp messages — just like you message a friend, except the "friend" is an AI bot running on your server.

**For the Farmer (The Consumer Experience):**
- A woman in Savelugu opens her regular WhatsApp (the same one she uses to message her daughter in Accra)
- She taps the New Chat button
- She types in ZAA's phone number: +233 55 123 4567 (this is your business number)
- She sends a voice note: "Naa, what is the price of shea butter today?"
- Within 3 seconds, she gets a voice note back in Dagbani: "Good morning Amina. Today in Savelugu market: ₵8 per kg. In Accra: ₵12 per kg. Would you like to sell?"

That is it. She did not download anything. She did not visit a website. She did not create a password. She just messaged a phone number.

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                         ZAA PLATFORM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  WhatsApp    │    │   Voice/SMS  │    │  Web Portal  │      │
│  │  Business API│    │   Fallback   │    │  (Buyers)    │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                    │               │
│         └───────────────────┼────────────────────┘               │
│                             │                                   │
│                    ┌────────┴────────┐                         │
│                    │  FastAPI Core   │                         │
│                    │   (Python)      │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐              │
│         │                   │                   │              │
│    ┌────┴────┐       ┌────┴────┐       ┌────┴────┐          │
│    │  AI     │       │  AI     │       │  AI     │          │
│    │ Speech  │       │ Vision  │       │  LLM    │          │
│    │ Layer   │       │ Grader  │       │  Core   │          │
│    │(Whisper)│       │(YOLO/   │       │(Llama 3)│          │
│    │(Piper)  │       │ ResNet) │       │         │          │
│    └────┬────┘       └────┬────┘       └────┬────┘          │
│         │                   │                   │              │
│         └───────────────────┼───────────────────┘              │
│                             │                                   │
│                    ┌────────┴────────┐                         │
│                    │   PostgreSQL    │                         │
│                    │   (Supabase)    │                         │
│                    └─────────────────┘                         │
│                             │                                   │
│                    ┌────────┴────────┐                         │
│                    │  MTN MoMo API   │                         │
│                    │   (Payments)    │                         │
│                    └─────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack
| Layer | Technology | Cost |
|-------|-----------|------|
| WhatsApp Bot | WhatsApp Cloud API | FREE (1,000 convos/month) |
| AI Speech | Whisper + Piper TTS | ~$0 (free tiers) |
| AI Vision | YOLOv8 / ResNet (fine-tuned) | FREE (HuggingFace) |
| AI Core | Llama 3 via Groq | FREE (20 req/min) |
| Backend | Python + FastAPI | FREE |
| Database | PostgreSQL (Supabase) | FREE (500MB) |
| Frontend | Next.js (Vercel) | FREE |
| Payments | MTN MoMo API | Pay-per-transaction |

### Directory Structure
```
zaa/
├── database/                # Database schema and migrations
│   └── schema.sql          # PostgreSQL schema with seed data
├── backend/                 # FastAPI application
│   ├── main.py             # Application entry point
│   ├── database.py         # Database connection and queries
│   ├── services/           # Business logic services
│   │   ├── ai_core.py      # AI intent processing (Llama 3 via Groq)
│   │   ├── ai_vision.py    # Image grading (YOLO/ResNet)
│   │   ├── translation.py  # Multi-language support (NLLB-200)
│   │   ├── listing_service.py  # Product listings
│   │   ├── bid_service.py  # Bidding and negotiations
│   │   ├── payment_service.py  # MTN MoMo payment processing
│   │   ├── group_service.py    # Group selling coordination
│   │   ├── market_data.py      # Market price data
│   │   ├── notification.py     # WhatsApp notifications
│   │   └── scheduler.py       # Background tasks (APScheduler)
│   └── routers/            # API route handlers
│       └── whatsapp.py     # WhatsApp webhook handler
├── frontend/               # Buyer dashboard (Next.js)
│   ├── app/
│   │   ├── page.tsx        # Landing page with dual interface info
│   │   ├── layout.tsx      # Root layout
│   │   └── dashboard/
│   │       ├── page.tsx    # Dashboard page (server component with metadata)
│   │       ├── BuyerDashboardClient.tsx  # Dashboard client component with React hooks
│   │       └── layout.tsx  # Dashboard layout
│   ├── public/             # Static assets
│   ├── package.json
│   ├── next.config.ts
│   └── tailwind.config.ts
├── docs/                   # Strategy, adoption, marketing
│   └── USER_MANUAL.md     # Complete user guide for farmers and buyers
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

### Getting Started
1. Install Python 3.10+, Node.js 18+
2. Copy `.env.example` to `.env` and fill in credentials
3. Run `pip install -r requirements.txt`
4. Run `cd backend && uvicorn main:app --reload`
5. Run `cd frontend && npm run dev` (for buyer dashboard)
6. Configure WhatsApp webhook URL to point to `/api/v1/whatsapp/webhook`

### The Two-Interface Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      FARMER INTERFACE                        │
│                     (WhatsApp Chat)                          │
│                                                              │
│   📱 Regular WhatsApp App → Messages ZAA phone number       │
│   🎙️ Voice notes in Dagbani/Twi/Gonja                       │
│   💬 Text replies in local languages                        │
│   📸 Photos of produce for AI grading                      │
│   💰 MoMo payments (no app needed)                          │
│                                                              │
│   NO APP TO DOWNLOAD. NO WEBSITE TO VISIT.                  │
│   NO PASSWORD. NO REGISTRATION FORM.                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              ↕ Your FastAPI Server (deployed)
┌─────────────────────────────────────────────────────────────┐
│                      BUYER INTERFACE                           │
│                  (Next.js Web Dashboard)                       │
│                                                              │
│   💻 Laptop/Tablet browser → https://zaa.com/dashboard       │
│   📊 Browse AI-graded listings                             │
│   🔍 Filter by commodity, grade, location                    │
│   💵 Place bids and manage escrow                            │
│   📈 View market analytics and price trends                   │
│                                                              │
│   THIS NEEDS TO BE BUILT AND DEPLOYED.                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### What You Need to Deploy vs What Already Exists
| Component | Already Exists? | What You Do |
|-----------|------------------|--------------|
| WhatsApp app on farmer's phone | ✅ Yes | Nothing. They already have it. |
| WhatsApp Business API | ✅ Yes (Meta provides it) | Register and configure. |
| Your FastAPI server | ❌ You build it | I gave you the code. Deploy to Render/Railway. |
| PostgreSQL database | ❌ You set it up | Use Supabase free tier. Run my schema.sql. |
| Buyer dashboard | ❌ You build it | I gave you the React code. Deploy to Vercel. |
| AI models (Llama 3, Whisper) | ✅ Yes (APIs) | Sign up for Groq and OpenAI free tiers. |
| MTN MoMo payments | ✅ Yes (MTN API) | Register for developer sandbox. |

### WhatsApp Business API Setup
**Step 1: Create a Meta Developer Account**
- Go to developers.facebook.com
- Create an app
- Add the "WhatsApp" product

**Step 2: Get a Business Phone Number**
- You can use a real phone number (buy a new MTN SIM for ₵10)
- Or use Meta's test number for development (free, but only you can message it)

**Step 3: Verify Your Business**
- Meta requires business verification to send messages to real users
- This takes 1-2 weeks
- You need a business registration document (or use your personal name initially)

**Step 4: Configure the Webhook**
- In the Meta dashboard, set your webhook URL: `https://your-server.com/api/v1/whatsapp/webhook`
- Meta sends a verification token. Your server must respond correctly (the verify_webhook function handles this)

**Step 5: Start Messaging**
- Once verified, any message sent to your business number gets forwarded to your server
- Your server processes it and replies

### Pricing Reality (What Meta Charges)
| Scenario | Cost |
|----------|------|
| User messages YOU first (initiates conversation) | FREE for the first 1,000 conversations per month |
| You message user first (send marketing/alert) | ~$0.005–$0.01 per message (varies by country) |
| Conversation window | 24 hours — any messages back-and-forth within 24h count as ONE conversation |

For ZAA: Since farmers will always message YOU first (they want prices, they want to sell), you will pay $0 for the first 1,000 users. After that, ~$5/month for every 1,000 additional users.

### Deployment Options
**Backend (FastAPI):**
- Render.com (free tier, easiest)
- Railway.app (free tier)
- DigitalOcean ($5/month droplet)

**Frontend (Next.js):**
- Vercel (free for Next.js)
- Netlify (free)

**Database:**
- Supabase (free tier - 500MB)

### Your Very First Step (This Weekend)
1. Go to developers.facebook.com
2. Create a developer account
3. Create a new app → Select "Business" type
4. Add "WhatsApp" product to your app
5. You will get a test phone number and a temporary access token
6. Copy the token into your .env file as WHATSAPP_TOKEN
7. Run the backend locally: `cd backend && uvicorn main:app --reload`
8. Use ngrok to expose your local server: `ngrok http 8000`
9. Set the webhook URL in Meta dashboard to your ngrok URL + /api/v1/whatsapp/webhook
10. Send a message to the test number from your own WhatsApp
11. Watch your server console log the incoming message
12. If you see the message in your terminal, you have proven the entire architecture works!

### MVP Timeline: 6 Weeks
- **Week 1-2**: WhatsApp Setup + Price Bot (Market prices integration)
- **Week 3-4**: Photo Grader (AI vision for shea/maize grading)
- **Week 5-6**: Marketplace + MoMo payments integration
- **Week 7-8**: Buyer dashboard deployment and testing
- **Week 9-10**: Production deployment and beta testing

### License
MIT - Built for Ghana, free for Africa.
