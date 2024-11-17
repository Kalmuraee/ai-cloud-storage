from datetime import datetime
from typing import Dict, List, Optional
import psutil
import logging
from prometheus_client import Counter, Gauge, Histogram
import aioredis

from app.core.config import settings

# Prometheus metrics
REQUESTS = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
ERRORS = Counter('http_errors_total', 'Total HTTP errors', ['method', 'endpoint', 'status'])
LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
STORAGE_USAGE = Gauge('storage_usage_bytes', 'Storage usage in bytes', ['bucket'])
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')

class MonitoringService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis = None

    async def start(self):
        """Initialize monitoring service."""
        try:
            self.redis = await aioredis.create_redis_pool(
                f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}'
            )
            # Start background tasks
            asyncio.create_task(self._collect_system_metrics())
        except Exception as e:
            self.logger.error(f"Failed to start monitoring service: {str(e)}")

    async def stop(self):
        """Cleanup monitoring service."""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    async def record_request(self, method: str, endpoint: str, duration: float, status: Optional[int] = None):
        """Record HTTP request metrics."""
        REQUESTS.labels(method=method, endpoint=endpoint).inc()
        LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
        
        if status and status >= 400:
            ERRORS.labels(method=method, endpoint=endpoint, status=status).inc()

    async def update_storage_metrics(self, bucket_usage: Dict[str, int]):
        """Update storage usage metrics."""
        for bucket, usage in bucket_usage.items():
            STORAGE_USAGE.labels(bucket=bucket).set(usage)

    async def _collect_system_metrics(self):
        """Collect system metrics periodically."""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent()
                CPU_USAGE.set(cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                MEMORY_USAGE.set(memory.used)

                # Store in Redis for historical data
                timestamp = datetime.now().timestamp()
                await self.redis.hset(
                    f'metrics:{int(timestamp)}',
                    mapping={
                        'cpu_usage': cpu_percent,
                        'memory_usage': memory.used
                    }
                )
                # Keep only last 24 hours of data
                await self.redis.expire(f'metrics:{int(timestamp)}', 86400)

            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {str(e)}")

            await asyncio.sleep(60)  # Collect every minute

    async def get_system_health(self) -> Dict:
        """Get system health status."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'status': 'healthy' if cpu_percent < 90 and memory.percent < 90 and disk.percent < 90 else 'warning',
                'cpu': {
                    'usage_percent': cpu_percent,
                    'status': 'healthy' if cpu_percent < 90 else 'warning'
                },
                'memory': {
                    'total': memory.total,
                    'used': memory.used,
                    'free': memory.free,
                    'usage_percent': memory.percent,
                    'status': 'healthy' if memory.percent < 90 else 'warning'
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'usage_percent': disk.percent,
                    'status': 'healthy' if disk.percent < 90 else 'warning'
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting system health: {str(e)}")
            return {'status': 'error', 'message': str(e)}

monitoring_service = MonitoringService()