import httpx
import os
import subprocess
import tempfile


def _wav_to_ogg(wav_bytes: bytes) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        wav_path = f.name
    ogg_path = wav_path.replace(".wav", ".ogg")
    try:
        subprocess.run(
            ["ffmpeg", "-i", wav_path, "-c:a", "libopus", "-b:a", "64k", ogg_path, "-y"],
            capture_output=True,
            check=True,
        )
        with open(ogg_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)
        if os.path.exists(ogg_path):
            os.unlink(ogg_path)


async def send_audio_message(phone_number_id: str, to: str, audio_bytes: bytes):
    token = os.getenv("WHATSAPP_TOKEN")
    base_url = f"https://graph.facebook.com/v20.0/{phone_number_id}"

    ogg_bytes = _wav_to_ogg(audio_bytes)

    async with httpx.AsyncClient(timeout=60.0) as client:
        upload = await client.post(
            f"{base_url}/media",
            headers={"Authorization": f"Bearer {token}"},
            data={"messaging_product": "whatsapp", "type": "audio/ogg"},
            files={"file": ("audio.ogg", ogg_bytes, "audio/ogg; codecs=opus")},
        )
        upload.raise_for_status()
        media_id = upload.json()["id"]

        response = await client.post(
            f"{base_url}/messages",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "audio",
                "audio": {"id": media_id},
            },
        )
        response.raise_for_status()


async def send_text_message(phone_number_id: str, to: str, text: str):
    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('WHATSAPP_TOKEN')}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
    return response.json()


async def download_media(media_id: str) -> bytes:
    token = os.getenv("WHATSAPP_TOKEN")

    async with httpx.AsyncClient() as client:
        url_response = await client.get(
            f"https://graph.facebook.com/v20.0/{media_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        url_response.raise_for_status()
        media_url = url_response.json()["url"]

        audio_response = await client.get(
            media_url,
            headers={"Authorization": f"Bearer {token}"},
        )
        audio_response.raise_for_status()
        return audio_response.content
