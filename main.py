import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import config
from services.firestore_service import seed_sample_data_if_empty
from routers.data_router import router as data_router
from routers.conversations_router import router as conversations_router
from routers.chat_router import router as chat_router
from routers.music_router import router as music_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Startup] Starting AI Assistant Backend Server...")
    # Seed 100 sample data points if database is empty
    seed_sample_data_if_empty()
    yield

app = FastAPI(
    title="나만의 AI 비서 API (Mood & Suno AI Music Assistant)",
    description="시계열 컨디션/기분 데이터 분석, Firestore CRUD, AI 챗봇(컨텍스트 주입), 선택형 Suno AI 음악 프롬프트 및 PC 다운로드 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Vercel & local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(data_router)
app.include_router(conversations_router)
app.include_router(chat_router)
app.include_router(music_router)

@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "online",
        "service": "AI Assistant Backend (Mood & Suno Music)",
        "version": "1.0.0"
    }

# Mount static files if index.html exists in root
project_dir = os.path.dirname(os.path.abspath(__file__))
index_html = os.path.join(project_dir, "index.html")

if os.path.exists(index_html):
    app.mount("/static", StaticFiles(directory=project_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(index_html)

    @app.get("/styles.css", include_in_schema=False)
    def serve_styles():
        return FileResponse(os.path.join(project_dir, "styles.css"))

    @app.get("/app.js", include_in_schema=False)
    def serve_app_js():
        return FileResponse(os.path.join(project_dir, "app.js"))

    @app.get("/favicon.ico", include_in_schema=False)
    def serve_favicon():
        favicon_path = os.path.join(project_dir, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path)
        from fastapi import Response
        return Response(status_code=204)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
