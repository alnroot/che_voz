from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

AGENT_MAP = {
    "MX": {
        "agent_id": "agent_mexico_123",
        "name": "Agente México",
        "context": "Eres un asistente amigable mexicano. Usa expresiones como 'qué onda', 'órale', 'sale'. Sé cálido y servicial.",
        "language": "es-MX"
    },
    "AR": {
        "agent_id": "agent_argentina_456",
        "name": "Agente Argentina", 
        "context": "Sos un asistente argentino copado. Usá 'che', 'boludo' (amigablemente), 'bárbaro'. Sé cordial y profesional.",
        "language": "es-AR"
    },
    "ES": {
        "agent_id": "agent_spain_789",
        "name": "Agente España",
        "context": "Eres un asistente español. Usa 'vale', 'tío/tía', 'guay'. Sé profesional pero cercano.",
        "language": "es-ES"
    },
    "US": {
        "agent_id": "agent_usa_101",
        "name": "US Agent",
        "context": "You're a friendly American assistant. Be professional, helpful, and use casual American expressions.",
        "language": "en-US"
    },
    "GB": {
        "agent_id": "agent_uk_102",
        "name": "UK Agent",
        "context": "You're a British assistant. Use British expressions like 'brilliant', 'cheers'. Be polite and professional.",
        "language": "en-GB"
    },
    "BR": {
        "agent_id": "agent_brazil_103",
        "name": "Agente Brasil",
        "context": "Você é um assistente brasileiro amigável. Use expressões como 'opa', 'beleza', 'valeu'. Seja cordial e prestativo.",
        "language": "pt-BR"
    }
}

DEFAULT_AGENT = AGENT_MAP["US"]


class AgentMapper:
    def __init__(self):
        self.agent_map = AGENT_MAP
        
    def get_agent_by_country(self, country_code: str) -> Dict[str, any]:
        agent = self.agent_map.get(country_code.upper(), DEFAULT_AGENT)
        logger.info(f"Mapped country {country_code} to agent {agent['name']}")
        return agent
    
    def get_agent_by_language(self, language_code: str) -> Dict[str, any]:
        for country, agent in self.agent_map.items():
            if agent["language"].lower() == language_code.lower():
                return agent
        return DEFAULT_AGENT
    
    def add_custom_agent(self, country_code: str, agent_config: Dict[str, any]):
        self.agent_map[country_code.upper()] = agent_config
        logger.info(f"Added custom agent for country {country_code}")


agent_mapper = AgentMapper()