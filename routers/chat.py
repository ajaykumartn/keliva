"""
Chat API Router
Handles web-based chat conversations for the frontend
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import logging

from services.conversation_service import (
    ConversationService,
    ConversationRequest
)
from utils.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


class ChatMessage(BaseModel):
    """Chat message from frontend"""
    message: str
    user_name: Optional[str] = "User"
    session_id: Optional[str] = None
    mode: Optional[str] = "chat"  # chat, grammar, voice


class ChatResponse(BaseModel):
    """Chat response to frontend"""
    response: str
    conversation_id: str
    language: str
    mode: str


@router.post("/conversation", response_model=ChatResponse)
async def chat_conversation(chat_message: ChatMessage):
    """
    Handle chat conversation from web frontend
    
    Args:
        chat_message: Chat message with text and metadata
        
    Returns:
        AI response with conversation details
    """
    try:
        service = get_conversation_service()
        
        # Get or create user for web session
        user_id = await service.get_or_create_user(
            telegram_id=None,
            session_id=chat_message.session_id or "web-session",
            name=chat_message.user_name,
            preferred_language="en"
        )
        
        # Create conversation request
        conv_request = ConversationRequest(
            user_id=user_id,
            user_name=chat_message.user_name,
            message=chat_message.message,
            interface="web",
            message_type="text",
            mode_context=chat_message.mode
        )
        
        # Process message through conversation pipeline
        response = await service.process_message(conv_request)
        
        # Create response with TTS instructions
        chat_response = ChatResponse(
            response=response.response_text,
            conversation_id=response.conversation_id,
            language=response.language.value,
            mode=chat_message.mode or "chat"
        )
        
        # Add TTS instructions to the response
        return {
            **chat_response.dict(),
            "tts": {
                "should_speak": True,
                "text": response.response_text,
                "voice_config": {
                    "voice": "en-US-AriaNeural" if response.language.value == "en" else "hi-IN-SwaraNeural",
                    "rate": 1.0,
                    "pitch": 1.0,
                    "volume": 1.0
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error in chat conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 20):
    """
    Get chat history for a web session
    
    Args:
        session_id: Web session identifier
        limit: Maximum number of messages to return
        
    Returns:
        List of conversation messages
    """
    try:
        service = get_conversation_service()
        
        # Find user by session ID
        user = db_manager.get_user_by_session_id(session_id)
        if not user:
            return {"messages": []}
        
        # Get conversation history
        history = service.get_conversation_history_for_user(
            user_id=user.id,
            limit=limit,
            include_all_interfaces=False
        )
        
        return {"messages": history}
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat history: {str(e)}"
        )


@router.post("/grammar/check")
async def check_grammar_web(chat_message: ChatMessage):
    """
    Grammar check endpoint for web frontend
    
    Args:
        chat_message: Message with text to check
        
    Returns:
        Grammar correction response
    """
    try:
        # Set mode to grammar for proper processing
        chat_message.mode = "grammar"
        
        # Use the same conversation endpoint but with grammar mode
        response = await chat_conversation(chat_message)
        
        return {
            "original_text": chat_message.message,
            "corrected_response": response.response,
            "conversation_id": response.conversation_id
        }
        
    except Exception as e:
        logger.error(f"Error in grammar check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check grammar: {str(e)}"
        )


@router.post("/voice/practice")
async def voice_practice_web(chat_message: ChatMessage):
    """
    Voice practice endpoint for web frontend
    
    Args:
        chat_message: Message with voice practice request
        
    Returns:
        Voice practice guidance response
    """
    try:
        # Set mode to voice for proper processing
        chat_message.mode = "voice"
        
        # Use the same conversation endpoint but with voice mode
        response = await chat_conversation(chat_message)
        
        return {
            "practice_text": chat_message.message,
            "guidance_response": response.response,
            "conversation_id": response.conversation_id
        }
        
    except Exception as e:
        logger.error(f"Error in voice practice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process voice practice: {str(e)}"
        )


@router.get("/health")
async def chat_health_check():
    """Health check for chat service"""
    try:
        service = get_conversation_service()
        return {
            "status": "ok",
            "service": "chat",
            "conversation_service": "initialized"
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "chat",
            "error": str(e)
        }