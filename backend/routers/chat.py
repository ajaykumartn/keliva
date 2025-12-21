"""
Chat API endpoints
Provides REST API for text-based conversations with Vani
"""
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os

from services.conversation_service import (
    ConversationService,
    ConversationRequest,
    ConversationResponse
)
from utils.db_manager import DatabaseManager


router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize services
conversation_service = None
db_manager = None


def get_conversation_service() -> ConversationService:
    """Lazy initialization of Conversation Service"""
    global conversation_service, db_manager
    if conversation_service is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GROQ_API_KEY not configured"
            )
        
        db_manager = DatabaseManager(db_path=os.getenv("DB_PATH", "keliva.db"))
        conversation_service = ConversationService(
            db_manager=db_manager,
            api_key=api_key,
            chroma_persist_dir=os.getenv("CHROMA_DB_PATH", "./chroma_db")
        )
    return conversation_service


# Request/Response models
class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message"""
    user_id: Optional[str] = Field(None, description="User identifier (if known)")
    session_id: Optional[str] = Field(None, description="Session ID for web users")
    telegram_id: Optional[int] = Field(None, description="Telegram user ID")
    user_name: str = Field(..., description="User's name")
    message: str = Field(..., min_length=1, max_length=5000, description="Message text")
    interface: str = Field(default="web", description="Interface type: web, telegram, or whatsapp")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID to continue existing conversation")
    message_type: str = Field(default="text", description="Message type: text or voice")


class ChatMessageResponse(BaseModel):
    """Response model for chat message"""
    response_text: str
    language: str
    conversation_id: str
    message_id: str
    emotional_tone: str
    facts_extracted: int
    concealment_applied: bool


class ConversationHistoryMessage(BaseModel):
    """Model for a single message in conversation history"""
    id: str
    role: str
    content: str
    language: str
    message_type: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history"""
    user_id: str
    conversation_id: Optional[str]
    messages: List[ConversationHistoryMessage]
    total_messages: int


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest):
    """
    Send a text message and receive AI response.
    
    This endpoint processes the message through the complete conversation pipeline:
    1. Detects language (English, Kannada, Telugu)
    2. Retrieves relevant context from Knowledge Vault
    3. Generates response using Vani persona
    4. Stores conversation in database
    5. Extracts and stores facts for future context
    
    Supports cross-platform user identification:
    - Web users: Use session_id
    - Telegram users: Use telegram_id
    - Existing users: Use user_id
    
    Uses Groq Llama 3.3 8B model (FREE - 14,000 requests/day).
    
    Args:
        request: ChatMessageRequest with user message and metadata
        
    Returns:
        ChatMessageResponse with AI response and metadata
        
    Raises:
        HTTPException: If API key is not configured or processing fails
    """
    try:
        service = get_conversation_service()
        
        # Get or create user based on provided identifiers
        if not request.user_id:
            user_id = await service.get_or_create_user(
                telegram_id=request.telegram_id,
                session_id=request.session_id,
                name=request.user_name,
                preferred_language="en"
            )
        else:
            user_id = request.user_id
        
        # Create conversation request
        conv_request = ConversationRequest(
            user_id=user_id,
            user_name=request.user_name,
            message=request.message,
            interface=request.interface,
            conversation_id=request.conversation_id,
            message_type=request.message_type
        )
        
        # Process message through conversation pipeline
        response = await service.process_message(conv_request)
        
        # Convert to response model
        return ChatMessageResponse(
            response_text=response.response_text,
            language=response.language.value,
            conversation_id=response.conversation_id,
            message_id=response.message_id,
            emotional_tone=response.emotional_tone.value,
            facts_extracted=response.facts_extracted,
            concealment_applied=response.concealment_applied
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Message processing failed: {str(e)}"
        )


@router.get("/history", response_model=ConversationHistoryResponse)
@router.get("/history/all", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    user_id: Optional[str] = Query(None, description="User identifier"),
    session_id: Optional[str] = Query(None, description="Session ID for web users"),
    telegram_id: Optional[int] = Query(None, description="Telegram user ID"),
    conversation_id: Optional[str] = Query(None, description="Optional specific conversation ID"),
    include_all_interfaces: bool = Query(False, description="Include messages from all interfaces (telegram, web, whatsapp)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of messages to retrieve")
):
    """
    Retrieve conversation history for a user.
    
    Supports cross-platform conversation continuity:
    - If include_all_interfaces=True, returns messages from ALL interfaces (telegram, web, whatsapp)
    - If conversation_id is provided, returns messages from that specific conversation
    - Otherwise, returns messages from the user's most recent conversation
    
    User identification (provide at least one):
    - user_id: Direct user identifier
    - session_id: Web session identifier
    - telegram_id: Telegram user identifier
    
    Args:
        user_id: User identifier (if known)
        session_id: Session ID for web users
        telegram_id: Telegram user ID
        conversation_id: Optional specific conversation ID
        include_all_interfaces: Include messages from all interfaces
        limit: Maximum number of messages (1-200, default 50)
        
    Returns:
        ConversationHistoryResponse with message history
        
    Raises:
        HTTPException: If user not found or retrieval fails
    """
    try:
        # Initialize database manager directly (don't need full conversation service for history)
        global db_manager
        if db_manager is None:
            db_manager = DatabaseManager(db_path=os.getenv("DB_PATH", "keliva.db"))
        
        # Resolve user_id if not provided
        if not user_id:
            if telegram_id:
                user = db_manager.get_user_by_telegram_id(telegram_id)
                if user:
                    user_id = user.id
            elif session_id:
                user = db_manager.get_user_by_session_id(session_id)
                if user:
                    user_id = user.id
            
            if not user_id:
                # Return empty history for new users instead of 404
                return ConversationHistoryResponse(
                    user_id=session_id or str(telegram_id) or "unknown",
                    conversation_id=None,
                    messages=[],
                    total_messages=0
                )
        
        # Get conversation history directly from database manager
        if conversation_id:
            # Get messages for specific conversation
            messages = db_manager.get_conversation_messages(
                conversation_id=conversation_id,
                limit=limit
            )
        elif include_all_interfaces:
            # Get messages across all conversations and interfaces
            messages = db_manager.get_user_messages_across_all_interfaces(
                user_id=user_id,
                limit=limit
            )
        else:
            # Get most recent conversation for user
            conversations = db_manager.get_user_conversations(
                user_id=user_id,
                limit=1
            )
            
            if not conversations:
                return ConversationHistoryResponse(
                    user_id=user_id,
                    conversation_id=None,
                    messages=[],
                    total_messages=0
                )
            
            messages = db_manager.get_conversation_messages(
                conversation_id=conversations[0].id,
                limit=limit
            )
        
        # Convert to response model
        message_responses = [
            ConversationHistoryMessage(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                language=msg.language,
                message_type=msg.message_type,
                timestamp=msg.timestamp.isoformat(),
                metadata=msg.metadata
            )
            for msg in messages
        ]
        
        return ConversationHistoryResponse(
            user_id=user_id,
            conversation_id=conversation_id,
            messages=message_responses,
            total_messages=len(message_responses)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation history: {str(e)}"
        )


@router.get("/history/unified", response_model=ConversationHistoryResponse)
async def get_unified_conversation_history(
    user_name: Optional[str] = Query(None, description="User name to find across all platforms"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of messages to retrieve")
):
    """
    Get unified conversation history across all platforms for a user by name.
    
    This endpoint finds all user accounts with the same name across different platforms
    (web, telegram, whatsapp) and returns their combined message history.
    
    Args:
        user_name: User name to search for across all platforms
        limit: Maximum number of messages (1-200, default 50)
        
    Returns:
        ConversationHistoryResponse with unified message history
    """
    try:
        global db_manager
        if db_manager is None:
            db_manager = DatabaseManager(db_path=os.getenv("DB_PATH", "keliva.db"))
        
        if not user_name:
            return ConversationHistoryResponse(
                user_id="unified",
                conversation_id=None,
                messages=[],
                total_messages=0
            )
        
        # Find all users with this name
        users = db_manager.find_users_by_name(user_name)
        
        if not users:
            return ConversationHistoryResponse(
                user_id=f"unified_{user_name}",
                conversation_id=None,
                messages=[],
                total_messages=0
            )
        
        # Get messages from all matching users
        all_messages = []
        for user in users:
            user_messages = db_manager.get_user_messages_across_all_interfaces(
                user_id=user.id,
                limit=limit
            )
            all_messages.extend(user_messages)
        
        # Sort by timestamp
        all_messages.sort(key=lambda x: x.timestamp)
        
        # Take only the most recent messages up to limit
        if len(all_messages) > limit:
            all_messages = all_messages[-limit:]
        
        # Convert to response model
        message_responses = [
            ConversationHistoryMessage(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                language=msg.language,
                message_type=msg.message_type,
                timestamp=msg.timestamp.isoformat(),
                metadata=msg.metadata
            )
            for msg in all_messages
        ]
        
        return ConversationHistoryResponse(
            user_id=f"unified_{user_name}",
            conversation_id=None,
            messages=message_responses,
            total_messages=len(message_responses)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve unified conversation history: {str(e)}"
        )


class UserContextRequest(BaseModel):
    """Request model for getting user context summary"""
    user_id: str
    query: Optional[str] = None


class UserContextResponse(BaseModel):
    """Response model for user context summary"""
    user_id: str
    total_facts: int
    entities: Dict[str, List[Dict[str, Any]]]


@router.post("/context", response_model=UserContextResponse)
async def get_user_context(request: UserContextRequest):
    """
    Get a summary of stored context (facts) for a user.
    
    This endpoint retrieves facts from the Knowledge Vault that have been
    extracted from previous conversations.
    
    Args:
        request: UserContextRequest with user_id and optional query
        
    Returns:
        UserContextResponse with facts grouped by entity
    """
    try:
        service = get_conversation_service()
        
        context_summary = await service.get_user_context_summary(
            user_id=request.user_id,
            query=request.query
        )
        
        return UserContextResponse(**context_summary)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user context: {str(e)}"
        )


class EndConversationRequest(BaseModel):
    """Request model for ending a conversation"""
    conversation_id: str


@router.post("/end")
async def end_conversation(request: EndConversationRequest):
    """
    Mark a conversation as ended.
    
    Args:
        request: EndConversationRequest with conversation_id
        
    Returns:
        Success message
    """
    try:
        service = get_conversation_service()
        service.end_conversation(request.conversation_id)
        
        return {
            "message": "Conversation ended successfully",
            "conversation_id": request.conversation_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end conversation: {str(e)}"
        )
