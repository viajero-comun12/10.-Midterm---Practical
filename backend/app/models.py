import re
from pydantic import BaseModel, Field, field_validator


class ShortenRequest(BaseModel):
    """Payload to create a new shortened URL."""
    original_url: str = Field(
        ...,
        description="The target web URL to be shortened",
        examples=["https://www.example.com/articulos/arquitectura-cloud"]
    )

    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        clean = v.strip()
        url_pattern = re.compile(
            r"^(https?://)"  # http:// or https://
            r"([A-Za-z0-9.-]+|\[[0-9a-fA-F:]+\])"  # domain or IPv6
            r"(:\d+)?"  # optional port
            r"(/.*)?$",  # optional path
            re.IGNORECASE
        )
        if not url_pattern.match(clean):
            raise ValueError("URL must start with http:// or https:// and be a valid URL")
        return clean


class ShortenResponse(BaseModel):
    """Response returned when a URL is shortened."""
    short_code: str = Field(..., description="Unique UUID identifying the shortened link")
    original_url: str = Field(..., description="Original destination URL")
    short_url: str = Field(..., description="Full shortened URL ready to be clicked or copied")


class UrlInfoResponse(BaseModel):
    """Metadata response for a shortened URL."""
    short_code: str = Field(..., description="Unique UUID of the link")
    original_url: str = Field(..., description="Original destination URL")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
