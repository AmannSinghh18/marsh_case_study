"""
FastAPI Main Application Entrypoint (Phase 4 Stage 4I & 4J)
Mounts REST API routes and static frontend dashboard files.
"""

import os
import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.api.routes import router

app = FastAPI(
    title="Marsh Insurance Case Study — Recommendation & Audit Engine",
    description="Evidence-grounded policy recommendation, claim audit, and pitch generation REST API.",
    version="1.0.0"
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router)

# Mount static frontend directory if present
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend_index():
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend index.html not found. Access API docs at /docs"}


def find_open_port(ports=(8000, 8050, 8001, 5000, 8888)):
    for port in ports:
        try:
            s = socket.socket()
            s.bind(('127.0.0.1', port))
            s.close()
            return port
        except Exception:
            continue
    return 8050


if __name__ == "__main__":
    import uvicorn

    selected_port = find_open_port()
    print(f"\n========================================================")
    print(f"  Starting Marsh Insurance Advisory Dashboard")
    print(f"  Open in browser: http://127.0.0.1:{selected_port}/")
    print(f"  API Documentation: http://127.0.0.1:{selected_port}/docs")
    print(f"========================================================\n")
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=selected_port, reload=True)
