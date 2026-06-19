import httpx
import base64
import os

DARI_STT_URL = os.getenv("DARI_STT_URL", "")
PASHTO_STT_URL = os.getenv("PASHTO_STT_URL", "")
DARI_TTS_URL = os.getenv("DARI_TTS_URL", "")
PASHTO_TTS_URL = os.getenv("PASHTO_TTS_URL", "")
STT_API_KEY = os.getenv("MODAL_STT_API_KEY")


async def transcribe_audio(audio_bytes: bytes, language: str = "dari") -> str:
    url = DARI_STT_URL if language == "dari" else PASHTO_STT_URL
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            url,
            headers={"X-API-Key": STT_API_KEY},
            json={"audio_base64": audio_base64},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("text") or data.get("transcription") or data.get("result") or ""


async def synthesize_speech(text: str, language: str = "dari") -> bytes:
    url = DARI_TTS_URL if language == "dari" else PASHTO_TTS_URL

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            url,
            headers={"X-API-Key": STT_API_KEY},
            json={"text": text},
        )
        response.raise_for_status()
        return response.content


async def ask_llm(user_text: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    bank_name = os.getenv("BANK_NAME", "our bank")

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=512,
        messages=[
            {
                "role": "system",
                "content": f"""You are a customer support agent for {bank_name}.
Your job is to help bank customers with their questions.
Always reply in the same language the customer used (Pashto or Dari).
Be polite, short, and clear.
If you cannot help with something, tell the customer to visit the nearest branch or call the helpline.
Do not make up account details, balances, or transaction information.""",
            },
            {"role": "user", "content": user_text},
        ],
    )
    return response.choices[0].message.content
