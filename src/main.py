from __future__ import annotations

from ai_copilot_serve.app import create_app
from ai_copilot_serve.core.config import get_settings

app = create_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "ai_copilot_serve.main:app",
        host=settings.copilot_host,
        port=settings.copilot_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
