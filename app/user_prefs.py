import modal

_store = modal.Dict.from_name("whatsapp-ai-agent-user-prefs", create_if_missing=True)


async def get_pref(phone: str) -> dict:
    return await _store.get.aio(phone, {})


async def set_pref(phone: str, key: str, value: str) -> None:
    current = await _store.get.aio(phone, {})
    current[key] = value
    await _store.__setitem__.aio(phone, current)
