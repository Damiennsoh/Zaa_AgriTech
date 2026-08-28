# 🌾 ZAA - The Voice-First AI Agricultural Exchange
## For Northern Ghana | Built by Ghanaians, For Africans

### What is ZAA?
ZAA (meaning "tomorrow" in Dagbani) is an AI-powered agricultural trading layer that lives inside WhatsApp. 
No apps to download. No smartphones required. No literacy needed.

A farmer in Walewale sends a voice note in Dagbani. ZAA understands, grades their produce from a photo, 
finds them a buyer, and ensures payment via MTN MoMo.

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
├── part1_database/          # Schema, migrations, seed data
├── part2_backend/           # FastAPI, WhatsApp handlers, API routes
├── part3_ai/                # Vision grading, speech, LLM prompts
├── part4_frontend/          # Buyer dashboard (Next.js)
├── part5_deployment/        # Docker, config, deployment scripts
└── docs/                    # Strategy, adoption, marketing
```

### Getting Started
1. Install Python 3.10+, Node.js 18+
2. Copy `.env.example` to `.env` and fill in credentials
3. Run `pip install -r requirements.txt`
4. Run `uvicorn main:app --reload`
5. Configure WhatsApp webhook URL

### MVP Timeline: 6 Weeks
- Week 1-2: Price Bot (WhatsApp + market prices)
- Week 3-4: Photo Grader (AI vision for shea/maize)
- Week 5-6: Marketplace + MoMo payments

### License
MIT - Built for Ghana, free for Africa.
