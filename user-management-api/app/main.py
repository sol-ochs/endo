import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.api.v1.endpoints import auth, users
from app.core.config import settings


logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="User Management API",
    description="User management backend for Endo UI",
    version="1.0.0",
    root_path=f"/{settings.ENVIRONMENT}"  # API Gateway stage prefix
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

app.include_router(auth.router, prefix="/v1/auth", tags=["authentication"])
app.include_router(users.router, prefix="/v1/users", tags=["users"])

# Lambda handler
handler = Mangum(app)