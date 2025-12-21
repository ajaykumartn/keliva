"""
Voice conversation router with WebSocket support
Handles real-time voice conversations with STT integration
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional
import json
import logging
import base64
import os
from datetime import datetime

from services.polyglot_engine import PolyglotEngine, Language
from services.tts_service import TTSService
from services.conversation_service import ConversationService, ConversationRequest
from utils.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Initialize services lazily to ensure environment variables are loaded
db_manager = None
polyglot_engine = None
tts_service = None
conversation_service = None

def get_services():
    """Lazy initialization of services after environment is loaded"""
    global db_manager, polyglot_engine, tts_service, conversation_service
    
    if db_manager is None:
        db_manager = DatabaseManager(db_path=os.getenv("DB_PATH", "keliva.db"))
        polyglot_engine = PolyglotEngine()
        tts_service = TTSService()
        conversation_service = ConversationService(
            db_manager=db_manager,
            chroma_persist_dir=os.getenv("CHROMA_DB_PATH", "./chroma_db")
        )
    
    return db_manager, polyglot_engine, tts_service, conversation_service


class ConnectionManager:
    """Manages WebSocket connections for voice calls"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, user_id: Optional[str] = None):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "conversation_id": None
        }
        logger.info(f"Client {client_id} connected (user_id: {user_id})")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    def get_metadata(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get connection metadata"""
        return self.connection_metadata.get(client_id)
    
    def update_metadata(self, client_id: str, key: str, value: Any):
        """Update connection metadata"""
        if client_id in self.connection_metadata:
            self.connection_metadata[client_id][key] = value


manager = ConnectionManager()


@router.websocket("/stream")
async def voice_stream_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice conversations.
    
    Implements Requirements 2.1, 2.2, 2.3, 2.4:
    - Bidirectional audio streaming
    - Real-time transcription handling
    - LLM response generation
    - TTS audio streaming
    
    Protocol:
    - Client sends: {"type": "init", "user_id": str, "user_name": str}
    - Client sends: {"type": "transcription", "text": str, "confidence": float, "language": str}
    - Server sends: {"type": "connected", "client_id": str}
    - Server sends: {"type": "transcription_received", "text": str}
    - Server sends: {"type": "response", "text": str, "language": str}
    - Server sends: {"type": "audio_chunk", "data": str, "sequence": int, "is_final": bool}
    - Server sends: {"type": "clarification_request", "message": str}
    - Server sends: {"type": "error", "message": str}
    """
    # Generate a simple client ID (in production, use proper session management)
    client_id = f"client_{id(websocket)}"
    
    await manager.connect(websocket, client_id)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "message": "WebSocket connection established"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "init":
                # Initialize connection with user information
                await handle_init(websocket, client_id, message)
            
            elif message_type == "transcription":
                # Handle transcribed text from Web Speech API
                await handle_transcription(websocket, client_id, message)
            
            elif message_type == "settings_update":
                # Handle settings update (voice gender, grammar mode)
                await handle_settings_update(websocket, client_id, message)
            
            elif message_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}", exc_info=True)
        manager.disconnect(client_id)
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        except:
            pass


async def handle_init(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """
    Handle connection initialization with user information.
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
        message: Init message with user_id, user_name, is_grammar_mode, voice_gender
    """
    user_id = message.get("user_id")
    user_name = message.get("user_name", "User")
    is_grammar_mode = message.get("is_grammar_mode", False)
    voice_gender = message.get("voice_gender", "male")  # 'male' for Pandu, 'female' for Chandu
    
    if not user_id:
        # Generate a temporary user ID if not provided
        user_id = f"temp_user_{client_id}"
        logger.warning(f"No user_id provided, using temporary: {user_id}")
    
    # Update connection metadata
    manager.update_metadata(client_id, "user_id", user_id)
    manager.update_metadata(client_id, "user_name", user_name)
    manager.update_metadata(client_id, "is_grammar_mode", is_grammar_mode)
    manager.update_metadata(client_id, "voice_gender", voice_gender)
    
    # Get services
    _, _, _, conv_service = get_services()
    
    # Get or create user in database
    db_user_id = await conv_service.get_or_create_user(
        name=user_name,
        preferred_language="en"
    )
    manager.update_metadata(client_id, "db_user_id", db_user_id)
    
    logger.info(f"Initialized connection for {client_id}: user_id={user_id}, user_name={user_name}, voice_gender={voice_gender}")
    
    await websocket.send_json({
        "type": "init_success",
        "message": f"Welcome {user_name}! Ready for voice conversation.",
        "user_id": user_id
    })


async def handle_settings_update(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """
    Handle settings update from client (voice gender, grammar mode).
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
        message: Settings update message
    """
    # Update voice gender if provided
    if "voice_gender" in message:
        voice_gender = message.get("voice_gender", "male")
        manager.update_metadata(client_id, "voice_gender", voice_gender)
        logger.info(f"Updated voice_gender for {client_id}: {voice_gender}")
    
    # Update grammar mode if provided
    if "is_grammar_mode" in message:
        is_grammar_mode = message.get("is_grammar_mode", False)
        manager.update_metadata(client_id, "is_grammar_mode", is_grammar_mode)
        logger.info(f"Updated is_grammar_mode for {client_id}: {is_grammar_mode}")
    
    await websocket.send_json({
        "type": "settings_updated",
        "message": "Settings updated successfully"
    })


async def handle_transcription(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """
    Handle transcribed text from Web Speech API.
    
    Implements complete voice pipeline:
    1. Validate transcription confidence (Requirement 11.5)
    2. Detect language (Requirement 3.1)
    3. Process through conversation service (Requirement 2.3)
    4. Generate TTS audio response (Requirement 2.4)
    5. Stream audio back to client (Requirement 12.5)
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
        message: Transcription message with text, confidence, and language
    """
    text = message.get("text", "")
    confidence = message.get("confidence", 1.0)
    detected_language = message.get("language", "en")
    
    logger.info(f"Received transcription from {client_id}: '{text}' (confidence: {confidence})")
    
    # Check confidence threshold (Requirement 11.5)
    if confidence < 0.6:
        # Request clarification for low-confidence transcriptions
        clarification_message = "I couldn't hear you clearly. Could you please repeat that?"
        
        await websocket.send_json({
            "type": "clarification_request",
            "message": clarification_message,
            "original_text": text,
            "confidence": confidence
        })
        
        # Also send TTS audio for clarification request
        try:
            await stream_tts_response(
                websocket=websocket,
                text=clarification_message,
                language=Language.ENGLISH
            )
        except Exception as e:
            logger.error(f"Failed to send clarification audio: {str(e)}")
        
        logger.info(f"Low confidence ({confidence}) - requesting clarification")
        return
    
    # Validate text has proper formatting (Requirement 11.4)
    if not text or not text.strip():
        await websocket.send_json({
            "type": "error",
            "message": "Empty transcription received"
        })
        return
    
    # Get connection metadata
    metadata = manager.get_metadata(client_id)
    if not metadata:
        await websocket.send_json({
            "type": "error",
            "message": "Connection not initialized. Please send init message first."
        })
        return
    
    user_id = metadata.get("db_user_id")
    user_name = metadata.get("user_name", "User")
    conversation_id = metadata.get("conversation_id")
    
    # Send acknowledgment that transcription was received
    await websocket.send_json({
        "type": "transcription_received",
        "text": text,
        "confidence": confidence
    })
    
    try:
        # Get services
        _, _, _, conv_service = get_services()
        
        # Process message through conversation service
        # This handles: language detection, context retrieval, LLM generation
        conversation_request = ConversationRequest(
            user_id=user_id,
            user_name=user_name,
            message=text,
            interface="web",
            conversation_id=conversation_id,
            message_type="voice"
        )
        
        response = await conv_service.process_message(conversation_request)
        
        # Update conversation ID in metadata
        if not conversation_id:
            manager.update_metadata(client_id, "conversation_id", response.conversation_id)
        
        # Send text response
        await websocket.send_json({
            "type": "response",
            "text": response.response_text,
            "language": response.language.value,
            "emotional_tone": response.emotional_tone.value,
            "conversation_id": response.conversation_id
        })
        
        # Stream TTS audio response (Requirement 2.4, 12.5)
        # If TTS fails, the text response is already sent above
        try:
            await stream_tts_response(
                websocket=websocket,
                text=response.response_text,
                language=response.language
            )
        except Exception as tts_error:
            logger.warning(f"TTS failed, but text response was sent: {str(tts_error)}")
            # Send notification that audio is unavailable
            await websocket.send_json({
                "type": "tts_unavailable",
                "message": "Audio playback unavailable, showing text only"
            })
        
        logger.info(f"Successfully processed voice message for {client_id}")
        
    except Exception as e:
        logger.error(f"Error processing transcription: {str(e)}", exc_info=True)
        
        error_message = "I'm having trouble processing your message. Could you try again?"
        
        await websocket.send_json({
            "type": "error",
            "message": error_message,
            "details": str(e)
        })
        
        # Try to send error message as audio
        try:
            await stream_tts_response(
                websocket=websocket,
                text=error_message,
                language=Language.ENGLISH
            )
        except:
            pass


async def stream_tts_response(
    websocket: WebSocket,
    text: str,
    language: Language
):
    """
    Stream TTS audio response to client.
    
    Implements Requirements 2.4, 12.5:
    - Convert text to speech
    - Stream audio chunks progressively
    - Minimize latency with chunked delivery
    
    Args:
        websocket: WebSocket connection
        text: Text to convert to speech
        language: Target language for TTS
    """
    try:
        # Get services
        _, _, tts, _ = get_services()
        
        # Generate and stream TTS audio
        async for audio_chunk in tts.text_to_speech(text, language, stream=True):
            # Encode audio data as base64 for JSON transmission
            if audio_chunk.data:
                audio_base64 = base64.b64encode(audio_chunk.data).decode('utf-8')
            else:
                audio_base64 = ""
            
            # Send audio chunk to client
            await websocket.send_json({
                "type": "audio_chunk",
                "data": audio_base64,
                "sequence": audio_chunk.sequence,
                "is_final": audio_chunk.is_final
            })
            
            # Log progress
            if audio_chunk.is_final:
                logger.info(f"Completed streaming {audio_chunk.sequence} audio chunks")
    
    except Exception as e:
        logger.error(f"Error streaming TTS audio: {str(e)}", exc_info=True)
        raise
