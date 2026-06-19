import modal

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "fastapi==0.115.0",
        "uvicorn==0.30.6",
        "httpx==0.27.2",
        "python-dotenv==1.0.1",
        "python-multipart==0.0.9",
        "aiofiles==24.1.0",
        "openai==1.51.0",
    )
    .add_local_dir("app", remote_path="/root/app")
)

app = modal.App("whatsapp-ai-agent")


@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
)
@modal.asgi_app()
def fastapi_app():
    import sys
    sys.path.insert(0, "/root")
    from app.main import app
    return app
