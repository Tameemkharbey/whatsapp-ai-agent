# BarakatPay WhatsApp AI Agent

A production-grade WhatsApp customer support agent for Afghan banking customers. Supports both **Dari (Afghan Persian)** and **Pashto** — via text or voice messages — deployed serverlessly on [Modal](https://modal.com).

## Architecture

```
WhatsApp User (text or voice)
        ↓
  Meta Cloud API (webhook POST)
        ↓
  FastAPI app  ──── Modal serverless
        ↓
  handler.py
   ├── text  → GPT-4o-mini → reply
   └── audio → Whisper INT8 (STT) → GPT-4o-mini → MB-iSTFT-VITS2 (TTS) → voice reply
```

The speech backend is provided by [pashto-dari-stt-tts](https://github.com/Tameemkharbey/pashto-dari-stt-tts), a separate Modal deployment running quantized Whisper and MB-iSTFT-VITS2 for both languages.

## Features

- **Bilingual** — Dari and Pashto with per-user language preference
- **Multimodal** — accepts voice notes and text; replies in voice or text per user choice
- **Banking context** — GPT-4o-mini system prompt scoped to customer support; never fabricates account data
- **Serverless** — zero-idle-cost Modal deployment with auto-scaling
- **Deduplication** — in-memory message ID set prevents double-processing of WhatsApp retries
- **Audio pipeline** — WAV → Opus/OGG re-encoding via FFmpeg before upload to Meta

## Tech Stack

| Layer | Technology |
|---|---|
| Webhook server | FastAPI + Uvicorn |
| Deployment | Modal (serverless ASGI) |
| LLM | OpenAI GPT-4o-mini |
| STT | Whisper INT8 via CTranslate2 (Modal endpoint) |
| TTS | MB-iSTFT-VITS2 (Modal endpoint) |
| Messaging | WhatsApp Business Cloud API (Meta Graph API v20) |
| Audio conversion | FFmpeg (WAV → Opus OGG) |

## Project Structure

```
app/
  main.py          # FastAPI app — webhook GET/POST endpoints
  handler.py       # Conversation state machine (lang → format → chat)
  whatsapp.py      # Meta API calls: send text, send audio, download media
  modal_client.py  # HTTP clients for Modal STT, TTS, and LLM endpoints
  user_prefs.py    # Per-user preference store (language + output format)
modal_deploy.py    # Modal app definition and deployment config
requirements.txt
SETUP.md           # Step-by-step local dev and Meta setup guide
```

## Quick Start

### Prerequisites
- Python 3.11+
- [Modal account](https://modal.com) with the CLI installed
- Meta Developer app with WhatsApp Business API enabled
- Deployed [pashto-dari-stt-tts](https://github.com/Tameemkharbey/pashto-dari-stt-tts) Modal endpoints

### Local development

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # fill in your secrets
uvicorn app.main:app --reload --port 8000
```

Expose locally with ngrok:
```bash
ngrok http 8000
```

### Deploy to Modal

```bash
pip install modal
modal deploy modal_deploy.py
```

Modal returns a public HTTPS URL — set this as your Meta webhook endpoint.

### Environment Variables

```env
WHATSAPP_TOKEN=           # Meta permanent token (from WhatsApp > API Setup)
WEBHOOK_VERIFY_TOKEN=     # Any random string; must match Meta webhook config
OPENAI_API_KEY=           # OpenAI API key

DARI_STT_URL=             # Modal endpoint: Dari Whisper
PASHTO_STT_URL=           # Modal endpoint: Pashto Whisper
DARI_TTS_URL=             # Modal endpoint: Dari MB-iSTFT-VITS2
PASHTO_TTS_URL=           # Modal endpoint: Pashto MB-iSTFT-VITS2
MODAL_STT_API_KEY=        # API key for Modal STT/TTS endpoints

BANK_NAME=                # Display name used in LLM system prompt
```

## User Flow

```
User sends first message
  └─ Agent asks: Dari (1) or Pashto (2)?
      └─ User picks language
          └─ Agent asks: Text (1) or Voice (2) replies?
              └─ User picks format → conversation begins
```

All subsequent messages (text or voice notes) are handled in the chosen language and output format until the user resets.

## Related Projects

- [pashto-dari-stt-tts](https://github.com/Tameemkharbey/pashto-dari-stt-tts) — the speech AI backend powering STT and TTS for this agent

## License

MIT
