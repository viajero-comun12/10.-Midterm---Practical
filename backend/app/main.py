import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("url_shortener")

app = FastAPI(
    title="AWS URL Shortener API",
    description=(
        "Backend REST API for URL shortener using AWS EC2, Amazon DynamoDB, and Amazon S3. "
        "Generates dynamic UUID short codes, persists them in DynamoDB, and executes real HTTP 307 redirects."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS so the S3 static frontend can call this backend
logger.info(f"Configuring CORS with origins: {settings.cors_origins_list}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def root_info():
    """Welcome and API documentation link."""
    return JSONResponse({
        "message": "AWS URL Shortener API is running",
        "documentation": "/docs",
        "endpoints": {
            "shorten_url": "POST /shorten",
            "redirect_url": "GET /{short_code}",
            "inspect_url": "GET /urls/{short_code}",
            "health_check": "GET /health"
        },
        "storage": "DynamoDB" if not settings.use_mock_db else "Mock In-Memory"
    })


# Include routes
app.include_router(router)
