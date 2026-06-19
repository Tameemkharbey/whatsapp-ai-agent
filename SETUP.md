# Setup & Run Guide

## Step 1 — Install dependencies
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2 — Fill in .env
Open `.env` and fill in:
- WHATSAPP_TOKEN → from Meta Developer dashboard
- WEBHOOK_VERIFY_TOKEN → make up any random string e.g. "mysecret123"
- MODAL_STT_URL → your Modal STT endpoint
- MODAL_LLM_URL → your Modal LLM endpoint

## Step 3 — Run the server
```
uvicorn app.main:app --reload --port 8000
```

## Step 4 — Expose with ngrok
In a second terminal:
```
ngrok http 8000
```
Copy the https URL it gives you, e.g.: https://abc123.ngrok-free.app

## Step 5 — Meta Developer Setup
1. Go to https://developers.facebook.com
2. Create an App → Business type
3. Add "WhatsApp" product
4. Go to WhatsApp > Configuration
5. Set Webhook URL: https://abc123.ngrok-free.app/webhook
6. Set Verify Token: same value as WEBHOOK_VERIFY_TOKEN in your .env
7. Click Verify — Meta will call your /webhook GET endpoint
8. Subscribe to "messages" field
9. Under "From number", add your personal WhatsApp number as a test number

## Step 6 — Test
Send a WhatsApp message (text or voice) to the test number Meta gives you.
Your agent will reply automatically.

## File Structure
```
app/
  main.py        → FastAPI app, webhook endpoints
  handler.py     → Routes text vs voice messages
  whatsapp.py    → Send messages, download media from Meta
  modal_client.py → Calls your Modal STT and LLM APIs
.env             → Your secrets (never commit this)
requirements.txt
```

## Adjusting modal_client.py
The two functions in modal_client.py need to match your actual Modal API:
- `transcribe_audio()` — check what field your STT returns the text in
- `ask_llm()` — check what field your LLM returns the response in
