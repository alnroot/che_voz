"""
Agent service using Factory pattern for agent management
"""
from typing import Dict, Optional
import logging

from infrastructure.agent_factory import ElevenLabsAgentFactory
from infrastructure.base_patterns import SingletonMeta
from domain.models import Agent

logger = logging.getLogger(__name__)


class AgentService(metaclass=SingletonMeta):
    """Singleton service for managing agents using Factory pattern"""
    
    def __init__(self):
        self._factory = ElevenLabsAgentFactory()
        logger.info("AgentService initialized with ElevenLabsAgentFactory")
    
    def get_agent_by_country(self, country_code: str) -> Agent:
        """Get agent for a specific country"""
        return self._factory.create_agent(country_code)
    
    def get_agent_by_language(self, language_code: str) -> Optional[Agent]:
        """Get agent for a specific language"""
        return self._factory.get_agent_by_language(language_code)
    
    def register_custom_agent(self, country_code: str, agent_config: Dict) -> None:
        """Register a custom agent configuration"""
        self._factory.register_agent(country_code, agent_config)
    
    def get_all_agents(self) -> Dict[str, Agent]:
        """Get all available agents"""
        return self._factory.get_available_agents()
    
    def get_agent_config(self, country_code: str) -> Dict:
        """Get agent configuration as dictionary (for backward compatibility)"""
        agent = self.get_agent_by_country(country_code)
        return agent.to_dict()


# Singleton instance
agent_service = AgentService()