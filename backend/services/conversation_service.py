"""
Conversation Service
Orchestrates all components for the core conversation flow:
- Language detection
- Knowledge Vault context retrieval
- Vani persona response generation
- Conversation history management
- Message persistence
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import uuid

from .polyglot_engine import PolyglotEngine, Language
from .knowledge_vault import KnowledgeVault, Fact
from .vani_persona import VaniPersona, ConversationContext, EmotionalTone, PersonaResponse

import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import (
    MessageCreate, MessageRole, MessageType, InterfaceType,
    ConversationCreate, UserCreate
)
from utils.db_manager import DatabaseManager


@dataclass
class ConversationRequest:
    """Request for processing a conversation message"""
    user_id: str
    user_name: str
    message: str
    interface: str = "telegram"  # "telegram", "whatsapp", or "web"
    conversation_id: Optional[str] = None
    message_type: str = "text"  # "text" or "voice"
    mode_context: Optional[str] = None  # "grammar", "chat", "vocabulary", "dreams", "practice"


@dataclass
class ConversationResponse:
    """Response from conversation processing"""
    response_text: str
    language: Language
    conversation_id: str
    message_id: str
    emotional_tone: EmotionalTone
    facts_extracted: int
    concealment_applied: bool


class ConversationService:
    """
    Core conversation service that orchestrates all components.
    Implements the text message processing pipeline:
    input → language detection → context retrieval → LLM → response
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        api_key: Optional[str] = None,
        chroma_persist_dir: str = "./chroma_db"
    ):
        """
        Initialize conversation service with all required components.
        
        Args:
            db_manager: Database manager for persistence
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            chroma_persist_dir: Directory for ChromaDB persistence
        """
        self.db_manager = db_manager
        
        # Initialize all service components
        self.polyglot_engine = PolyglotEngine(api_key=api_key)
        self.knowledge_vault = KnowledgeVault(
            api_key=api_key,
            persist_directory=chroma_persist_dir
        )
        self.vani_persona = VaniPersona(api_key=api_key)
    
    async def process_message(self, request: ConversationRequest) -> ConversationResponse:
        """
        Processes a user message through the complete conversation pipeline.
        
        Pipeline:
        1. Detect language of input
        2. Get or create conversation
        3. Retrieve conversation history
        4. Extract and store facts from user message
        5. Retrieve relevant context from Knowledge Vault
        6. Generate response using Vani persona
        7. Store user message and assistant response
        8. Return response
        
        Args:
            request: ConversationRequest with user message and metadata
            
        Returns:
            ConversationResponse with generated response and metadata
        """
        # Step 1: Detect language
        detected_language = await self.polyglot_engine.detect_language(request.message)
        
        # Step 2: Get or create conversation
        conversation_id = await self._get_or_create_conversation(
            request.user_id,
            request.conversation_id,
            request.interface
        )
        
        # Step 3: Retrieve conversation history
        conversation_history = self._get_conversation_history(conversation_id)
        
        # Step 4: Extract and store facts from user message
        facts = await self.knowledge_vault.extract_facts(
            user_id=request.user_id,
            message=request.message,
            conversation_history=conversation_history
        )
        
        # Store extracted facts
        for fact in facts:
            await self.knowledge_vault.store_fact(fact)
        
        # Step 5: Retrieve relevant context from Knowledge Vault
        retrieved_facts = await self.knowledge_vault.retrieve_context(
            query=request.message,
            user_id=request.user_id,
            top_k=5
        )
        
        # Step 6: Generate response using Vani persona
        # Determine if we're in grammar mode based on user's selected mode
        # Only enable grammar mode if explicitly requested, not just for English detection
        is_grammar_mode = (request.mode_context == "grammar")
        
        context = ConversationContext(
            user_name=request.user_name,
            user_message=request.message,
            language=detected_language,
            conversation_history=conversation_history,
            retrieved_facts=retrieved_facts,
            emotional_tone=EmotionalTone.NEUTRAL,  # Auto-detected in persona
            is_grammar_mode=is_grammar_mode,
            mode_context=request.mode_context,
            interface=request.interface
        )
        
        persona_response = await self.vani_persona.generate_response(context)
        
        # Step 7: Store user message and assistant response
        user_message_id = self._store_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=request.message,
            language=detected_language.value,
            message_type=request.message_type
        )
        
        assistant_message_id = self._store_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=persona_response.content,
            language=persona_response.language.value,
            message_type=request.message_type,
            metadata={
                "emotional_tone": persona_response.emotional_tone.value,
                "concealment_applied": persona_response.concealment_applied,
                "facts_retrieved": len(retrieved_facts)
            }
        )
        
        # Update user's last active timestamp
        self.db_manager.update_user_last_active(request.user_id)
        
        # Step 8: Return response
        return ConversationResponse(
            response_text=persona_response.content,
            language=persona_response.language,
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            emotional_tone=persona_response.emotional_tone,
            facts_extracted=len(facts),
            concealment_applied=persona_response.concealment_applied
        )
    
    async def _get_or_create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str],
        interface: str
    ) -> str:
        """
        Gets existing conversation or creates a new one.
        
        Args:
            user_id: User identifier
            conversation_id: Optional existing conversation ID
            interface: Interface type (telegram, whatsapp, web)
            
        Returns:
            Conversation ID
        """
        # If conversation_id provided, verify it exists
        if conversation_id:
            conversation = self.db_manager.get_conversation(conversation_id)
            if conversation:
                return conversation_id
        
        # Create new conversation
        conversation_create = ConversationCreate(
            user_id=user_id,
            interface=interface
        )
        
        conversation = self.db_manager.create_conversation(conversation_create)
        return conversation.id
    
    def _get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Retrieves conversation history formatted for LLM context.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        messages = self.db_manager.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit
        )
        
        # Format for LLM context
        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return history
    
    def _store_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        language: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Stores a message in the database.
        
        Args:
            conversation_id: Conversation identifier
            role: Message role (user or assistant)
            content: Message content
            language: Language code
            message_type: Type of message (text or voice)
            metadata: Optional metadata dictionary
            
        Returns:
            Message ID
        """
        message_create = MessageCreate(
            conversation_id=conversation_id,
            role=role.value,
            content=content,
            language=language,
            message_type=message_type,
            metadata=metadata
        )
        
        message = self.db_manager.create_message(message_create)
        return message.id
    
    def get_conversation_history_for_user(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        limit: int = 50,
        include_all_interfaces: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieves conversation history for display to user.
        Supports cross-platform conversation continuity.
        
        Args:
            user_id: User identifier
            conversation_id: Optional specific conversation ID
            limit: Maximum number of messages to retrieve
            include_all_interfaces: If True, includes messages from all interfaces (telegram, web, whatsapp)
            
        Returns:
            List of message dictionaries with full details
        """
        if conversation_id:
            # Get messages for specific conversation
            messages = self.db_manager.get_conversation_messages(
                conversation_id=conversation_id,
                limit=limit
            )
        elif include_all_interfaces:
            # Get messages across all conversations and interfaces
            messages = self.db_manager.get_user_messages_across_all_interfaces(
                user_id=user_id,
                limit=limit
            )
        else:
            # Get most recent conversation for user
            conversations = self.db_manager.get_user_conversations(
                user_id=user_id,
                limit=1
            )
            
            if not conversations:
                return []
            
            messages = self.db_manager.get_conversation_messages(
                conversation_id=conversations[0].id,
                limit=limit
            )
        
        # Format for API response
        history = []
        for msg in messages:
            history.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "language": msg.language,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            })
        
        return history
    
    async def get_or_create_user(
        self,
        telegram_id: Optional[int] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
        preferred_language: str = "en"
    ) -> str:
        """
        Gets existing user or creates a new one.
        Supports both Telegram ID (for messaging) and session ID (for web).
        
        Args:
            telegram_id: Optional Telegram user ID
            session_id: Optional web session ID
            name: Optional user name
            preferred_language: Preferred language code
            
        Returns:
            User ID
        """
        # Try to find existing user by Telegram ID
        if telegram_id:
            user = self.db_manager.get_user_by_telegram_id(telegram_id)
            if user:
                return user.id
        
        # Try to find existing user by session ID
        if session_id:
            user = self.db_manager.get_user_by_session_id(session_id)
            if user:
                return user.id
        
        # Create new user
        user_create = UserCreate(
            telegram_id=telegram_id,
            session_id=session_id,
            name=name,
            preferred_language=preferred_language
        )
        
        user = self.db_manager.create_user(user_create)
        return user.id
    
    def end_conversation(self, conversation_id: str) -> None:
        """
        Marks a conversation as ended.
        
        Args:
            conversation_id: Conversation identifier
        """
        self.db_manager.end_conversation(conversation_id)
    
    async def extract_and_store_facts_manually(
        self,
        user_id: str,
        text: str
    ) -> List[Fact]:
        """
        Manually extracts and stores facts from text.
        Useful for batch processing or admin operations.
        
        Args:
            user_id: User identifier
            text: Text to extract facts from
            
        Returns:
            List of extracted and stored facts
        """
        facts = await self.knowledge_vault.extract_facts(
            user_id=user_id,
            message=text,
            conversation_history=None
        )
        
        for fact in facts:
            await self.knowledge_vault.store_fact(fact)
        
        return facts
    
    async def get_user_context_summary(
        self,
        user_id: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gets a summary of stored context for a user.
        
        Args:
            user_id: User identifier
            query: Optional query to filter relevant facts
            
        Returns:
            Dictionary with context summary
        """
        if query:
            # Get relevant facts for query
            facts = await self.knowledge_vault.retrieve_context(
                query=query,
                user_id=user_id,
                top_k=10
            )
        else:
            # Get all facts
            facts = self.knowledge_vault.get_all_facts(user_id=user_id)
        
        # Group facts by entity
        entities = {}
        for fact in facts:
            if fact.entity not in entities:
                entities[fact.entity] = []
            entities[fact.entity].append({
                "relation": fact.relation,
                "attribute": fact.attribute,
                "value": fact.value,
                "context": fact.context,
                "timestamp": fact.timestamp.isoformat()
            })
        
        return {
            "user_id": user_id,
            "total_facts": len(facts),
            "entities": entities
        }
