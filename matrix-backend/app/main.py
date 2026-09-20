import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import uploads, settings, generate

app = FastAPI(
    title="Matrix — Question Paper Maker API",
    description="Backend for the MatrAIx-Persona-8B–powered question paper generator.",
    version="0.1.0",
)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(uploads.router)
app.include_router(settings.router)
app.include_router(generate.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
