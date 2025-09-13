import redis.asyncio as redis
import json
import logging
from typing import Dict, Optional, Any
from config.settings import settings

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self):
        self._client = None
        
    async def get_client(self):
        if not self._client:
            self._client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client
    
    async def set_call_context(self, call_sid: str, context: Dict[str, Any], ttl: int = 3600):
        client = await self.get_client()
        key = f"call:{call_sid}"
        await client.setex(key, ttl, json.dumps(context))
        logger.info(f"Set call context for {call_sid}")
    
    async def get_call_context(self, call_sid: str) -> Optional[Dict[str, Any]]:
        client = await self.get_client()
        key = f"call:{call_sid}"
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def delete_call_context(self, call_sid: str):
        client = await self.get_client()
        key = f"call:{call_sid}"
        await client.delete(key)
        logger.info(f"Deleted call context for {call_sid}")
    
    async def set_websocket_mapping(self, websocket_id: str, call_sid: str, ttl: int = 3600):
        client = await self.get_client()
        key = f"ws:{websocket_id}"
        await client.setex(key, ttl, call_sid)
    
    async def get_call_sid_from_websocket(self, websocket_id: str) -> Optional[str]:
        client = await self.get_client()
        key = f"ws:{websocket_id}"
        return await client.get(key)
    
    async def close(self):
        if self._client:
            await self._client.close()


redis_service = RedisService()