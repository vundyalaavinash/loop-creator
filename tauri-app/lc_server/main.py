from __future__ import annotations
import argparse
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lc_server.routes import loops as loops_routes
from lc_server.routes import files as files_routes
from lc_server.routes import context as context_routes


def create_app() -> FastAPI:
    app = FastAPI(title="Loop Creator Server", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["tauri://localhost", "http://localhost:5173", "http://localhost:*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"ok": True}

    app.include_router(loops_routes.router)
    app.include_router(files_routes.router)
    app.include_router(context_routes.router)

    return app


app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
