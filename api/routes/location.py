"""
Location-based suggestions API routes
"""
from fastapi import APIRouter, Request
from typing import Dict, Optional
import httpx
import logging

from services.location_service import LocationService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/suggest-agent")
async def suggest_agent(request: Request) -> Dict:
    """
    Suggest an agent based on the user's location
    Uses IP geolocation as primary method
    """
    try:
        # Get client IP
        client_ip = request.client.host
        
        # Handle local development
        if client_ip in ['127.0.0.1', 'localhost', '::1']:
            # Try to get real IP from headers (for proxied requests)
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                client_ip = forwarded_for.split(',')[0].strip()
            else:
                # Return default for local testing
                return {
                    "success": True,
                    "location": {
                        "country_code": "AR",
                        "country_name": "Argentina",
                        "city": "Buenos Aires"
                    },
                    "suggestion": {
                        "agent_code": "111",
                        "agent_info": {
                            "name": "Agente Porteño",
                            "flag": "🇦🇷",
                            "region": "Buenos Aires"
                        },
                        "message": "Detectamos que estás en Buenos Aires, Argentina. Te sugerimos hablar con 🇦🇷 Agente Porteño!"
                    }
                }
        
        # Call IP geolocation service
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://ipapi.co/{client_ip}/json/",
                timeout=5.0
            )
            
            if response.status_code == 200:
                geo_data = response.json()
                
                country_code = geo_data.get('country_code', '')
                country_name = geo_data.get('country_name', '')
                city = geo_data.get('city', '')
                
                # Get suggested agent
                agent_code, agent_info = LocationService.get_suggested_agent(
                    country_code, city
                )
                
                # Generate message
                message = LocationService.get_location_message(
                    country_name, city, agent_info
                )
                
                return {
                    "success": True,
                    "location": {
                        "country_code": country_code,
                        "country_name": country_name,
                        "city": city,
                        "region": geo_data.get('region', ''),
                        "latitude": geo_data.get('latitude'),
                        "longitude": geo_data.get('longitude')
                    },
                    "suggestion": {
                        "agent_code": agent_code,
                        "agent_info": agent_info,
                        "message": message
                    }
                }
            else:
                raise Exception(f"Geolocation API returned {response.status_code}")
                
    except Exception as e:
        logger.error(f"Error getting location suggestion: {str(e)}")
        
        # Return default suggestion on error
        return {
            "success": False,
            "error": str(e),
            "suggestion": {
                "agent_code": "111",
                "agent_info": {
                    "name": "Agente Porteño",
                    "flag": "🇦🇷",
                    "region": "Buenos Aires"
                },
                "message": "No pudimos detectar tu ubicación. Puedes elegir cualquier agente!"
            }
        }

@router.post("/suggest-agent-by-location")
async def suggest_agent_by_location(location_data: Dict) -> Dict:
    """
    Suggest an agent based on provided location data
    Useful when frontend has access to more precise location
    """
    try:
        country_code = location_data.get('country_code', '')
        city = location_data.get('city', '')
        
        # Get suggested agent
        agent_code, agent_info = LocationService.get_suggested_agent(
            country_code, city
        )
        
        # Generate message
        country_name = location_data.get('country_name', country_code)
        message = LocationService.get_location_message(
            country_name, city, agent_info
        )
        
        return {
            "success": True,
            "suggestion": {
                "agent_code": agent_code,
                "agent_info": agent_info,
                "message": message
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing location data: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "suggestion": {
                "agent_code": "111",
                "agent_info": {
                    "name": "Agente Porteño",
                    "flag": "🇦🇷",
                    "region": "Buenos Aires"
                },
                "message": "Error procesando ubicación. Puedes elegir cualquier agente!"
            }
        }