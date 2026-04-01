from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    """Open the MongoDB connection. Called on application startup."""
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    # Verify connectivity with a lightweight command
    await _client.admin.command("ping")
    logger.info("Connected to MongoDB at %s", settings.mongodb_uri)


async def close_db() -> None:
    """Close the MongoDB connection. Called on application shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Return the application database. Raises RuntimeError if not connected."""
    if _client is None:
        raise RuntimeError("MongoDB client is not initialised. Call connect_db() first.")
    return _client[get_settings().mongodb_db_name]
