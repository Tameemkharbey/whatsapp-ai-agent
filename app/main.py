import os
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from app.handler import handle_message
from app.whatsapp import send_text_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

_seen_message_ids: set[str] = set()


@app.get("/")
async def root():
    return {"status": "WhatsApp AI Agent running"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == os.getenv("WEBHOOK_VERIFY_TOKEN"):
        return PlainTextResponse(content=challenge)
    return PlainTextResponse(content="Forbidden", status_code=403)


async def _safe_handle(from_number: str, message: dict, message_type: str, phone_number_id: str):
    try:
        await handle_message(
            from_number=from_number,
            message=message,
            message_type=message_type,
            phone_number_id=phone_number_id,
        )
    except Exception as e:
        logger.error(f"handle_message failed for {from_number}: {e}", exc_info=True)
        try:
            await send_text_message(phone_number_id, from_number, f"[Error] {e}")
        except Exception as send_err:
            logger.error(f"send_text_message also failed: {send_err}")


@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            return {"status": "ignored"}

        message = value["messages"][0]
        message_id = message.get("id", "")

        if message_id in _seen_message_ids:
            return {"status": "duplicate"}
        _seen_message_ids.add(message_id)
        if len(_seen_message_ids) > 1000:
            _seen_message_ids.clear()

        from_number = message["from"]
        message_type = message["type"]
        phone_number_id = value["metadata"]["phone_number_id"]

        background_tasks.add_task(
            _safe_handle,
            from_number=from_number,
            message=message,
            message_type=message_type,
            phone_number_id=phone_number_id,
        )

    except (KeyError, IndexError):
        pass

    return {"status": "ok"}
