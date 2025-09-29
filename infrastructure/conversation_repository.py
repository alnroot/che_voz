from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path
import asyncio

from models.conversation import ConversationHistory, ConversationSummary, ConversationMessage


class ConversationRepository(ABC):
    """Abstract repository for conversation persistence"""
    
    @abstractmethod
    async def save(self, conversation: ConversationHistory) -> bool:
        pass
    
    @abstractmethod
    async def find_by_id(self, conversation_id: str) -> Optional[ConversationHistory]:
        pass
    
    @abstractmethod
    async def find_by_phone(self, phone_number: str) -> List[ConversationSummary]:
        pass
    
    @abstractmethod
    async def find_recent(self, limit: int = 10) -> List[ConversationSummary]:
        pass
    
    @abstractmethod
    async def update(self, conversation_id: str, data: Dict[str, Any]) -> bool:
        pass


class FileSystemConversationRepository(ConversationRepository):
    """File system based repository for conversation persistence"""
    
    def __init__(self, base_path: str = "./conversations"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self._lock = asyncio.Lock()
    
    def _get_conversation_path(self, conversation_id: str) -> Path:
        return self.base_path / f"{conversation_id}.json"
    
    async def save(self, conversation: ConversationHistory) -> bool:
        async with self._lock:
            try:
                file_path = self._get_conversation_path(conversation.conversation_id)
                data = conversation.model_dump_json(indent=2)
                
                # Write atomically
                temp_path = file_path.with_suffix('.tmp')
                with open(temp_path, 'w') as f:
                    f.write(data)
                temp_path.rename(file_path)
                return True
            except Exception as e:
                import logging
                logging.error(f"Failed to save conversation: {e}")
                return False
    
    async def find_by_id(self, conversation_id: str) -> Optional[ConversationHistory]:
        try:
            file_path = self._get_conversation_path(conversation_id)
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return ConversationHistory(**data)
            return None
        except Exception:
            return None
    
    async def find_by_phone(self, phone_number: str) -> List[ConversationSummary]:
        summaries = []
        
        for file_path in self.base_path.glob("*.json"):
            if file_path.suffix == ".json":
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if data.get("caller_phone") == phone_number:
                        conv = ConversationHistory(**data)
                        summaries.append(self._create_summary(conv))
                except Exception:
                    continue
        
        summaries.sort(key=lambda x: x.start_time, reverse=True)
        return summaries
    
    async def find_recent(self, limit: int = 10) -> List[ConversationSummary]:
        summaries = []
        
        # Get files sorted by modification time
        files_with_mtime = []
        for file_path in self.base_path.glob("*.json"):
            if file_path.suffix == ".json":
                files_with_mtime.append((file_path, file_path.stat().st_mtime))
        
        files_with_mtime.sort(key=lambda x: x[1], reverse=True)
        
        # Load the most recent ones
        for file_path, _ in files_with_mtime[:limit]:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                conv = ConversationHistory(**data)
                summaries.append(self._create_summary(conv))
            except Exception:
                continue
        
        return summaries
    
    async def update(self, conversation_id: str, data: Dict[str, Any]) -> bool:
        async with self._lock:
            conv = await self.find_by_id(conversation_id)
            if conv:
                for key, value in data.items():
                    if hasattr(conv, key):
                        setattr(conv, key, value)
                return await self.save(conv)
            return False
    
    def _create_summary(self, conv: ConversationHistory) -> ConversationSummary:
        return ConversationSummary(
            conversation_id=conv.conversation_id,
            caller_phone=conv.caller_phone,
            caller_name=conv.caller_name,
            agent_id=conv.agent_id,
            agent_name=conv.agent_name,
            country_code=conv.country_code,
            language=conv.language,
            start_time=conv.start_time,
            end_time=conv.end_time,
            duration_seconds=int((conv.end_time - conv.start_time).total_seconds()) if conv.end_time else 0,
            message_count=len(conv.messages),
            status=conv.status
        )