"""
Location-based agent suggestion service
"""
from typing import Dict, Optional, Tuple
import re

class LocationService:
    """Service for suggesting agents based on location"""
    
    # Country to default agent mapping
    COUNTRY_AGENTS = {
        'AR': '111',  # Argentina -> Porteño
        'MX': '222',  # México -> Mexicano
        'CO': '333',  # Colombia -> Colombiana
        'ES': '222',  # España -> Mexicano (Spanish neutral)
        'PE': '333',  # Perú -> Colombiana (closest accent)
        'CL': '111',  # Chile -> Porteño (closest accent)
        'UY': '111',  # Uruguay -> Porteño (closest accent)
        'PY': '111',  # Paraguay -> Porteño (closest accent)
        'BO': '333',  # Bolivia -> Colombiana
        'EC': '333',  # Ecuador -> Colombiana
        'VE': '333',  # Venezuela -> Colombiana
        'PA': '333',  # Panamá -> Colombiana
        'CR': '222',  # Costa Rica -> Mexicano
        'GT': '222',  # Guatemala -> Mexicano
        'HN': '222',  # Honduras -> Mexicano
        'SV': '222',  # El Salvador -> Mexicano
        'NI': '222',  # Nicaragua -> Mexicano
        'DO': '333',  # República Dominicana -> Colombiana
        'PR': '333',  # Puerto Rico -> Colombiana
        'CU': '333',  # Cuba -> Colombiana
    }
    
    # City/Region specific mappings for Argentina
    ARGENTINA_REGIONS = {
        # Córdoba and surroundings
        'córdoba': '444',
        'cordoba': '444',
        'villa carlos paz': '444',
        'río cuarto': '444',
        'villa maría': '444',
        
        # Mendoza and Cuyo region
        'mendoza': '555',
        'san rafael': '555',
        'san juan': '555',
        'san luis': '555',
        
        # Buenos Aires (default to Porteño)
        'buenos aires': '111',
        'capital federal': '111',
        'caba': '111',
        'la plata': '111',
        'mar del plata': '111',
        
        # Other regions default to Porteño
        'rosario': '111',
        'santa fe': '111',
        'tucumán': '111',
        'salta': '111',
    }
    
    @classmethod
    def get_suggested_agent(cls, country_code: str, city: Optional[str] = None) -> Tuple[str, Dict[str, str]]:
        """
        Get suggested agent based on location
        
        Returns:
            Tuple of (agent_code, agent_info)
        """
        # Normalize inputs
        country_code = country_code.upper() if country_code else ''
        city = city.lower() if city else ''
        
        # Special handling for Argentina with city detection
        if country_code == 'AR' and city:
            # Check for specific city/region matches
            for location, agent_code in cls.ARGENTINA_REGIONS.items():
                if location in city:
                    return agent_code, cls._get_agent_info(agent_code)
        
        # Get country-based suggestion
        agent_code = cls.COUNTRY_AGENTS.get(country_code, '111')  # Default to Porteño
        return agent_code, cls._get_agent_info(agent_code)
    
    @staticmethod
    def _get_agent_info(agent_code: str) -> Dict[str, str]:
        """Get agent information by code"""
        agents = {
            '111': {'name': 'Agente Porteño', 'flag': '🇦🇷', 'region': 'Buenos Aires'},
            '222': {'name': 'Agente Mexicano', 'flag': '🇲🇽', 'region': 'México'},
            '333': {'name': 'Agente Colombiana', 'flag': '🇨🇴', 'region': 'Colombia'},
            '444': {'name': 'Agente Cordobés', 'flag': '🇦🇷', 'region': 'Córdoba'},
            '555': {'name': 'Agente Mendocino', 'flag': '🇦🇷', 'region': 'Mendoza'},
        }
        return agents.get(agent_code, agents['111'])
    
    @classmethod
    def get_location_message(cls, country_name: str, city: Optional[str], agent_info: Dict[str, str]) -> str:
        """Generate a friendly location-based message"""
        if city:
            return f"Detectamos que estás en {city}, {country_name}. Te sugerimos hablar con {agent_info['flag']} {agent_info['name']}!"
        else:
            return f"Detectamos que estás en {country_name}. Te sugerimos hablar con {agent_info['flag']} {agent_info['name']}!"