"""
Rate limiting middleware using Redis
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from redis import Redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Redis connection for rate limiting
redis_client = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

# Create limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["200/minute"]
)

# Custom rate limit for SMS to protect budget
async def check_sms_budget(limit: int = 1000) -> bool:
    """Check if daily SMS budget exceeded"""
    key = "sms:daily:count"
    count = redis_client.get(key)
    
    if count is None:
        redis_client.setex(key, 86400, 1)
        return True
    
    count = int(count)
    if count >= limit:
        logger.warning(f"Daily SMS budget exceeded: {count}/{limit}")
        return False
    
    redis_client.incr(key)
    return True


async def check_employee_sms_limit(employee_id: str, limit: int = 10) -> bool:
    """Check if employee exceeded hourly SMS limit"""
    key = f"sms:employee:{employee_id}:hourly"
    count = redis_client.get(key)
    
    if count is None:
        redis_client.setex(key, 3600, 1)
        return True
    
    count = int(count)
    if count >= limit:
        logger.warning(f"Employee {employee_id} exceeded hourly SMS limit: {count}/{limit}")
        return False
    
    redis_client.incr(key)
    return True
