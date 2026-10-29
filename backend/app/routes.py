import uuid
from datetime import datetime, timezone
import logging
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.database import db
from app.models import ShortenRequest, ShortenResponse, UrlInfoResponse, ErrorResponse

logger = logging.getLogger("url_shortener.routes")

router = APIRouter()


@router.get(
    "/health",
    summary="Health check endpoint",
    tags=["Monitoring"]
)
def health_check():
    """Health check endpoint used by monitoring tools and load balancers."""
    return {
        "status": "healthy",
        "service": "aws-url-shortener-api",
        "storage_mode": "mock" if db.is_mock else "dynamodb",
        "table": settings.dynamodb_table,
        "region": settings.aws_region
    }


@router.post(
    "/shorten",
    response_model=ShortenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a shortened URL",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL supplied"},
        500: {"model": ErrorResponse, "description": "Database or server error"}
    },
    tags=["URL Shortener"]
)
def create_short_url(payload: ShortenRequest, request: Request):
    """Endpoint 1: Create a short URL.

    - Receives original URL.
    - Generates a unique UUID v4.
    - Persists UUID, original_url, and created_at in DynamoDB.
    - Returns short_code, original_url, and short_url.
    """
    try:
        # Generate dynamic UUID
        short_code = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        original_url = str(payload.original_url)

        # Persist to DynamoDB
        db.save_url(short_code=short_code, original_url=original_url, created_at=created_at)

        # Build short_url: prioritize settings.base_url, fallback to request host if default
        base = settings.clean_base_url
        short_url = f"{base}/{short_code}"

        return ShortenResponse(
            short_code=short_code,
            original_url=original_url,
            short_url=short_url
        )
    except Exception as e:
        logger.error(f"Error creating short URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to shorten URL: {str(e)}"
        )


@router.get(
    "/urls/{short_code}",
    response_model=UrlInfoResponse,
    summary="Inspect shortened URL metadata",
    responses={
        404: {"model": ErrorResponse, "description": "Short code not found"}
    },
    tags=["URL Shortener"]
)
def get_url_info(short_code: str):
    """Endpoint 3: Retrieve information about a shortened URL.

    - Queries DynamoDB by short_code.
    - Returns JSON with short_code, original_url, and created_at.
    - Returns 404 Not Found if not found.
    """
    try:
        item = db.get_url(short_code=short_code)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"URL with code '{short_code}' not found."
            )

        return UrlInfoResponse(
            short_code=item["short_code"],
            original_url=item["original_url"],
            created_at=item["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying URL info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query error: {str(e)}"
        )


@router.get(
    "/{short_code}",
    summary="Redirect to original URL",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    response_class=RedirectResponse,
    responses={
        307: {"description": "Temporary Redirect to destination URL"},
        404: {"model": ErrorResponse, "description": "Short URL does not exist"}
    },
    tags=["URL Redirection"]
)
def redirect_to_original(short_code: str):
    """Endpoint 2: Redirect to original destination.

    - Main shortener functionality.
    - Receives UUID from path.
    - Queries DynamoDB to find corresponding record.
    - Retrieves original_url.
    - Responds with HTTP 307 Temporary Redirect.
    - Returns 404 Not Found if UUID does not exist.
    """
    try:
        item = db.get_url(short_code=short_code)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Short URL '{short_code}' does not exist or has expired."
            )

        destination = item["original_url"]
        logger.info(f"Redirecting {short_code} -> {destination}")
        return RedirectResponse(
            url=destination,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during redirection lookup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Redirection error: {str(e)}"
        )
