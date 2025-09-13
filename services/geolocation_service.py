import httpx
import logging
from typing import Dict, Optional
from config.settings import settings
import redis.asyncio as redis
import json

logger = logging.getLogger(__name__)


class GeolocationService:
    def __init__(self):
        self.numverify_api_key = settings.numverify_api_key
        self.redis_client = None
        self.base_url = "http://apilayer.net/api/validate"
        
    async def initialize(self):
        self.redis_client = await redis.from_url(settings.redis_url)
        
    async def get_location(self, phone_number: str) -> Dict[str, any]:
        if not self.redis_client:
            await self.initialize()
            
        cache_key = f"location:{phone_number}"
        
        cached = await self.redis_client.get(cache_key)
        if cached:
            logger.info(f"Location cache hit for {phone_number}")
            return json.loads(cached)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "access_key": self.numverify_api_key,
                        "number": phone_number,
                        "country_code": "",
                        "format": 1
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("valid"):
                        location_data = {
                            "country_code": data.get("country_code"),
                            "country_name": data.get("country_name"),
                            "location": data.get("location"),
                            "carrier": data.get("carrier"),
                            "line_type": data.get("line_type")
                        }
                        
                        await self.redis_client.setex(
                            cache_key,
                            86400,  # Cache for 24 hours
                            json.dumps(location_data)
                        )
                        
                        return location_data
                        
        except Exception as e:
            logger.error(f"Error getting location for {phone_number}: {str(e)}")
        
        return {"country_code": "US", "country_name": "United States"}


geolocation_service = GeolocationService()