from __future__ import annotations

from app import build_asgi_app

app = build_asgi_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.copilot_host,
        port=settings.copilot_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
