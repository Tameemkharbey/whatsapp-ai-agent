from app.whatsapp import send_text_message, send_audio_message, download_media
from app.modal_client import transcribe_audio, synthesize_speech, ask_llm
from app.user_prefs import get_pref, set_pref

LANG_PROMPT = (
    "سلام! خوش آمدید.\n"
    "لطفاً زبان خود را انتخاب کنید:\n"
    "1 - دری\n"
    "2 - پښتو"
)

FORMAT_PROMPT = {
    "dari": "ممنون! پاسخ‌ها را چطور دریافت کنید؟\n1 - متن\n2 - صدا",
    "pashto": "مننه! ځوابونه څنګه غواړئ؟\n1 - متن\n2 - غږ",
}

CONFIRMED_FORMAT = {
    ("dari", "text"): "✅ آماده‌ام! چطور کمکتان کنم؟",
    ("dari", "voice"): "✅ آماده‌ام! چطور کمکتان کنم؟",
    ("pashto", "text"): "✅ چمتو یم! څنګه درسره مرسته وکړم؟",
    ("pashto", "voice"): "✅ چمتو یم! څنګه درسره مرسته وکړم؟",
}

AUDIO_ERROR = {
    "dari": "متأسفم، صدا را متوجه نشدم. لطفاً دوباره تلاش کنید.",
    "pashto": "بښنه غواړم، غږ مې ونه پوهاوه. مهرباني وکړئ بیا هڅه وکړئ.",
}

UNSUPPORTED = {
    "dari": "لطفاً پیام متنی یا صوتی ارسال کنید.",
    "pashto": "مهرباني وکړئ متني یا غږیز پیام واستوئ.",
}


async def _reply(phone_number_id: str, to: str, text: str, lang: str, output: str):
    if output == "voice":
        audio_bytes = await synthesize_speech(text, lang)
        await send_audio_message(phone_number_id, to, audio_bytes)
    else:
        await send_text_message(phone_number_id, to, text)


async def handle_message(
    from_number: str,
    message: dict,
    message_type: str,
    phone_number_id: str,
):
    pref = await get_pref(from_number)
    step = pref.get("step")

    # ── Step 1: Language selection ──────────────────────────────────────────
    if not step or step == "lang":
        if message_type == "text":
            choice = message["text"]["body"].strip()
            if choice == "1":
                await set_pref(from_number, "lang", "dari")
                await set_pref(from_number, "step", "format")
                await send_text_message(phone_number_id, from_number, FORMAT_PROMPT["dari"])
                return
            if choice == "2":
                await set_pref(from_number, "lang", "pashto")
                await set_pref(from_number, "step", "format")
                await send_text_message(phone_number_id, from_number, FORMAT_PROMPT["pashto"])
                return
        await send_text_message(phone_number_id, from_number, LANG_PROMPT)
        return

    # ── Step 2: Output format selection ─────────────────────────────────────
    if step == "format":
        lang = pref.get("lang", "dari")
        if message_type == "text":
            choice = message["text"]["body"].strip()
            if choice == "1":
                await set_pref(from_number, "output", "text")
                await set_pref(from_number, "step", "ready")
                await send_text_message(phone_number_id, from_number, CONFIRMED_FORMAT[(lang, "text")])
                return
            if choice == "2":
                await set_pref(from_number, "output", "voice")
                await set_pref(from_number, "step", "ready")
                await send_text_message(phone_number_id, from_number, CONFIRMED_FORMAT[(lang, "voice")])
                return
        await send_text_message(phone_number_id, from_number, FORMAT_PROMPT[lang])
        return

    # ── Step 3: Normal conversation ──────────────────────────────────────────
    lang = pref.get("lang", "dari")
    output = pref.get("output", "text")

    if message_type == "text":
        user_text = message["text"]["body"].strip()
        reply = await ask_llm(user_text)
        await _reply(phone_number_id, from_number, reply, lang, output)
        return

    if message_type == "audio":
        media_id = message["audio"]["id"]
        audio_bytes = await download_media(media_id)
        user_text = await transcribe_audio(audio_bytes, lang)

        if not user_text:
            await send_text_message(phone_number_id, from_number, AUDIO_ERROR[lang])
            return

        reply = await ask_llm(user_text)
        await _reply(phone_number_id, from_number, reply, lang, output)
        return

    await send_text_message(phone_number_id, from_number, UNSUPPORTED.get(lang, UNSUPPORTED["dari"]))
