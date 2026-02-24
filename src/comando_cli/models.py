"""Data models for the streaming CLI."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MediaType(str, Enum):
    """Type of media."""

    MOVIE = "movie"
    SERIES = "series"


class Episode(BaseModel):
    """Episode information."""

    number: int
    title: Optional[str] = None
    duration: Optional[int] = None  # in seconds


class QualityOption(BaseModel):
    """Quality/language variant for content."""

    quality: str  # e.g., "720p", "1080p"
    language: str  # e.g., "Portuguese", "English"
    magnet_link: str


class Title(BaseModel):
    """Movie or TV series title information."""

    id: str  # Unique identifier (usually from URL)
    name: str
    media_type: MediaType
    url: str
    poster_url: Optional[str] = None
    synopsis: Optional[str] = None
    episodes: list[Episode] = Field(default_factory=list)
    quality_options: list[QualityOption] = Field(default_factory=list)


class WatchHistory(BaseModel):
    """Watch history record."""

    id: int = Field(default=0)  # SQLite row id
    title_id: str
    title_name: str
    media_type: MediaType
    last_episode: Optional[int] = None  # For series: last watched episode
    last_watched_date: datetime = Field(default_factory=datetime.now)
    duration_seconds: int = 0  # Video duration in seconds
    position_seconds: int = 0  # Last watched position in seconds

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}
