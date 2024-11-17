from datetime import datetime
import logging
from typing import Dict, Optional
import aioredis

from app.core.config import settings
from app.services.minio import minio_service

class QuotaService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis = None
        self.default_quota = settings.DEFAULT_USER_QUOTA  # in bytes

    async def start(self):
        """Initialize quota service."""
        try:
            self.redis = await aioredis.create_redis_pool(
                f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}'
            )
        except Exception as e:
            self.logger.error(f"Failed to start quota service: {str(e)}")

    async def stop(self):
        """Cleanup quota service."""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    async def get_quota(self, user_id: int) -> Dict:
        """Get user's quota information."""
        try:
            # Get quota limit
            quota_limit = await self.redis.get(f'quota:limit:{user_id}')
            quota_limit = int(quota_limit) if quota_limit else self.default_quota
            
            # Get current usage
            usage = await self.redis.get(f'quota:usage:{user_id}')
            usage = int(usage) if usage else 0
            
            return {
                'limit': quota_limit,
                'used': usage,
                'available': quota_limit - usage,
                'usage_percent': (usage / quota_limit) * 100 if quota_limit > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to get quota for user {user_id}: {str(e)}")
            raise

    async def set_quota(self, user_id: int, quota_bytes: int) -> None:
        """Set user's quota limit."""
        try:
            await self.redis.set(f'quota:limit:{user_id}', quota_bytes)
        except Exception as e:
            self.logger.error(f"Failed to set quota for user {user_id}: {str(e)}")
            raise

    async def check_quota(self, user_id: int, size: int) -> bool:
        """Check if operation would exceed quota."""
        try:
            quota_info = await self.get_quota(user_id)
            return size <= quota_info['available']
        except Exception as e:
            self.logger.error(f"Failed to check quota for user {user_id}: {str(e)}")
            raise

    async def update_usage(self, user_id: int, size_delta: int) -> None:
        """Update user's storage usage."""
        try:
            # Update usage atomically
            await self.redis.incrby(f'quota:usage:{user_id}', size_delta)
            
            # If removing storage (negative delta), ensure we don't go below 0
            if size_delta < 0:
                await self.redis.set(
                    f'quota:usage:{user_id}',
                    max(0, int(await self.redis.get(f'quota:usage:{user_id}') or 0))
                )
        except Exception as e:
            self.logger.error(f"Failed to update usage for user {user_id}: {str(e)}")
            raise

    async def recalculate_usage(self, user_id: int) -> None:
        """Recalculate user's storage usage from actual bucket contents."""
        try:
            total_size = 0
            buckets = await minio_service.list_buckets()
            
            for bucket in buckets:
                # Only count buckets owned by this user
                if str(user_id) in bucket.name:  # Assuming bucket names contain user ID
                    objects = await minio_service.list_objects(bucket.name)
                    bucket_size = sum(obj.size for obj in objects)
                    total_size += bucket_size
            
            # Update Redis with recalculated usage
            await self.redis.set(f'quota:usage:{user_id}', total_size)
            
        except Exception as e:
            self.logger.error(f"Failed to recalculate usage for user {user_id}: {str(e)}")
            raise

    async def get_all_quotas(self) -> Dict[int, Dict]:
        """Get quota information for all users."""
        try:
            # Get all user IDs from quota keys
            user_keys = await self.redis.keys('quota:limit:*')
            user_ids = [int(key.split(':')[-1]) for key in user_keys]
            
            quotas = {}
            for user_id in user_ids:
                quotas[user_id] = await self.get_quota(user_id)
            
            return quotas
        except Exception as e:
            self.logger.error(f"Failed to get all quotas: {str(e)}")
            raise

quota_service = QuotaService()