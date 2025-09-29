from abc import ABC, abstractmethod
from typing import Dict, Optional, Protocol
import logging

from domain.models import Agent

logger = logging.getLogger(__name__)


class AgentProtocol(Protocol):
    """Protocol defining what an agent implementation must provide"""
    agent_id: str
    name: str
    language: str
    context: str
    country_code: str
    api_key: Optional[str]
    
    def to_dict(self) -> Dict:
        ...


class AbstractAgentFactory(ABC):
    """Abstract factory for creating agents"""
    
    @abstractmethod
    def create_agent(self, country_code: str) -> Agent:
        """Create an agent based on country code"""
        pass
    
    @abstractmethod
    def register_agent(self, country_code: str, agent_config: Dict) -> None:
        """Register a new agent configuration"""
        pass
    
    @abstractmethod
    def get_available_agents(self) -> Dict[str, Agent]:
        """Get all available agents"""
        pass


class ElevenLabsAgentFactory(AbstractAgentFactory):
    """Concrete factory for creating ElevenLabs agents"""
    
    def __init__(self):
        self._agents: Dict[str, Dict] = {}
        self._default_country = "AR"
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize default agent configurations"""
        default_agents = {
            "AR": {
                "agent_id": "agent_3601k52aw9jmej0a61svgk2hm0t1",
                "name": "Agente Porteño", 
                "context": "Sos un asistente argentino copado. Usá 'che', 'boludo' (amigablemente), 'bárbaro'. Sé cordial y profesional.",
                "language": "es-AR"
            },
            "AR_CBA": {
                "agent_id": "agent_4201k59pp9k7epq8t6pq5n79b9k1",
                "name": "Agente Cordobés",
                "context": "Sos un asistente cordobés muy copado. Usá 'culia', 'qué tal', 'todo joya'. Sé amigable y relajado como un verdadero cordobés.",
                "language": "es-AR"
            },
            "MX": {
                "agent_id": "agent_3601k52b7a5nff29cgwj04h3m0xt",
                "name": "Agente Mexicano",
                "context": "Eres un asistente amigable mexicano. Usa expresiones como 'qué onda', 'órale', 'sale'. Sé cálido y servicial.",
                "language": "es-MX"
            },
            "CO": {
                "agent_id": "agent_2201k52bqy0bff2ag591exhzjaxf",
                "name": "Agente Colombiana",
                "context": "Eres una asistente colombiana amigable. Usa expresiones como 'parcero', 'qué más', 'bacano'. Sé cálida y servicial.",
                "language": "es-CO"
            },
            "MENDOCINO": {
                "agent_id": "agent_7601k57zdzznesfrwpf8hfpemjvf",
                "name": "Mendocino", 
                "context": "[Context is configured in ElevenLabs - this field is informational only]",
                "language": "es-AR"
            }
        }
        
        for country_code, config in default_agents.items():
            self._agents[country_code] = config
    
    def create_agent(self, country_code: str) -> Agent:
        """Create an agent instance based on country code"""
        country_code_upper = country_code.upper()
        
        if country_code_upper not in self._agents:
            logger.warning(f"Country code {country_code} not found, using default")
            country_code_upper = self._default_country
        
        config = self._agents[country_code_upper]
        
        agent = Agent(
            agent_id=config["agent_id"],
            name=config["name"],
            language=config["language"],
            context=config["context"],
            country_code=country_code_upper,
            api_key=config.get("api_key")
        )
        
        logger.info(f"Created agent {agent.name} for country {country_code}")
        return agent
    
    def register_agent(self, country_code: str, agent_config: Dict) -> None:
        """Register a new agent configuration"""
        required_fields = ["agent_id", "name", "language", "context"]
        
        for field in required_fields:
            if field not in agent_config:
                raise ValueError(f"Missing required field: {field}")
        
        self._agents[country_code.upper()] = agent_config
        logger.info(f"Registered new agent for country {country_code}")
    
    def get_available_agents(self) -> Dict[str, Agent]:
        """Get all available agents as Agent instances"""
        return {
            code: self.create_agent(code) 
            for code in self._agents.keys()
        }
    
    def get_agent_by_language(self, language_code: str) -> Optional[Agent]:
        """Get the first agent that matches the language code"""
        for country_code, config in self._agents.items():
            if config["language"].lower() == language_code.lower():
                return self.create_agent(country_code)
        return None