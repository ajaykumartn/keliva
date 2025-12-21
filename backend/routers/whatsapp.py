"""
WhatsApp Integration via Twilio
Provides webhook endpoint for receiving messages from WhatsApp
"""
from fastapi import APIRouter, HTTPException, Request, Form, status
from typing import Optional
import os
import logging
import httpx
import tempfile
import base64
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import json

from services.conversation_service import (
    ConversationService,
    ConversationRequest
)
from services.stt_service import create_stt_service
from utils.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# Initialize services
conversation_service = None
db_manager = None
twilio_client = None
stt_service = None

# User session storage (in production, use Redis or database)
whatsapp_user_sessions = {}


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


def get_twilio_client() -> Client:
    """Get Twilio client"""
    global twilio_client
    if twilio_client is None:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        if not account_sid or not auth_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Twilio credentials not configured"
            )
        
        twilio_client = Client(account_sid, auth_token)
    return twilio_client


def get_stt_service():
    """Lazy initialization of STT Service"""
    global stt_service
    if stt_service is None:
        stt_service = create_stt_service()
    return stt_service


def get_whatsapp_user_session(phone_number: str) -> dict:
    """Get or create WhatsApp user session"""
    if phone_number not in whatsapp_user_sessions:
        whatsapp_user_sessions[phone_number] = {
            "mode": "menu",  # menu, grammar, chat, vocabulary, dreams, practice
            "language": "en",
            "conversation_history": []
        }
    return whatsapp_user_sessions[phone_number]


def set_whatsapp_user_mode(phone_number: str, mode: str):
    """Set WhatsApp user's current mode"""
    session = get_whatsapp_user_session(phone_number)
    session["mode"] = mode
    whatsapp_user_sessions[phone_number] = session





async def send_interactive_menu(phone_number: str) -> bool:
    """Send interactive menu with clickable buttons via Twilio API"""
    try:
        client = get_twilio_client()
        
        # For now, Twilio's Interactive Messages API requires special setup
        # Let's use a simple button-based approach that works reliably
        
        # Create quick reply buttons (these work without special configuration)
        message_body = """👋 Hello! I'm Captain, your AI companion.

🎯 *Choose what you'd like to do:*

Reply with the number or tap a button below:"""

        # Send message with simple text menu
        # Ensure proper WhatsApp formatting for both From and To
        from_number = os.getenv("TWILIO_PHONE_NUMBER")
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
            
        message = client.messages.create(
            from_=from_number,
            to=f"whatsapp:{phone_number}",
            body=message_body
        )
        
        logger.info(f"Sent interactive menu to {phone_number}: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send interactive menu: {e}")
        # Return False to trigger fallback to text menu
        return False


async def send_interactive_buttons(phone_number: str, text: str, buttons: list) -> bool:
    """Send interactive buttons via Twilio API"""
    try:
        client = get_twilio_client()
        
        # For now, use simple text with visual buttons
        # Real interactive buttons require Twilio Business API approval
        
        button_text = text + "\n\n_Tap to reply:_"
        for i, button in enumerate(buttons, 1):
            if isinstance(button, dict) and "reply" in button:
                title = button["reply"].get("title", f"Option {i}")
                button_text += f"\n• {title}"
        
        # Ensure proper WhatsApp formatting for both From and To
        from_number = os.getenv("TWILIO_PHONE_NUMBER")
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
            
        message = client.messages.create(
            from_=from_number,
            to=f"whatsapp:{phone_number}",
            body=button_text
        )
        
        logger.info(f"Sent interactive buttons to {phone_number}: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send interactive buttons: {e}")
        return False


def create_whatsapp_menu_message() -> str:
    """Create WhatsApp menu message (fallback for non-interactive)"""
    return """👋 Hello! I'm Captain, your AI companion.

🎯 *Choose what you'd like to do:*

*1* ✏️ Grammar Check
Fix your English writing

*2* 💬 General Chat  
Casual conversation

*3* 📚 Vocabulary
Learn new words

*4* 🌙 Dream Journal
Share and analyze dreams

*5* 🎓 Language Practice
Structured exercises

💡 *Just type the number (1-5)!*
🎤 *Voice chat:* https://keliva-app.pages.dev"""


async def send_mode_activation_with_button(phone_number: str, mode: str) -> bool:
    """Send mode activation message with back button"""
    mode_messages = {
        "grammar": "✏️ *Grammar Check Mode Activated!*\n\n📝 Send me any English text and I'll fix grammar errors, improve sentence structure, and explain corrections.\n\n💡 *Example:* \"I are going to school yesterday\"",
        "chat": "💬 *General Chat Mode Activated!*\n\n🌍 Let's have a friendly conversation! Talk in English, Kannada, or Telugu. Ask me anything!\n\n😊 What's on your mind today?",
        "vocabulary": "📚 *Vocabulary Learning Mode Activated!*\n\n🎯 I'll help you expand your vocabulary with meanings, examples, and pronunciation tips.\n\n💡 *Try:* \"What does 'serendipity' mean?\"",
        "dreams": "🌙 *Dream Journal Mode Activated!*\n\n✨ Share your dreams and I'll provide psychological interpretations and symbolic analysis.\n\n💭 *Just describe your dream...*",
        "practice": "🎓 *Language Practice Mode Activated!*\n\n📖 Get structured learning activities, grammar exercises, and pronunciation guidance.\n\n🎯 *Try:* \"Give me a grammar exercise\""
    }
    
    message_text = mode_messages.get(mode, "Mode activated!")
    
    # Create back button
    back_button = [
        {
            "type": "reply",
            "reply": {
                "id": "back_to_menu",
                "title": "🔙 Back to Menu"
            }
        }
    ]
    
    # Try to send with interactive button
    success = await send_interactive_buttons(phone_number, message_text, back_button)
    return success


def create_mode_activation_message(mode: str) -> str:
    """Create mode activation message for WhatsApp"""
    mode_messages = {
        "grammar": """✏️ *Grammar Check Mode Activated!*

📝 Send me any English text and I'll:

• Fix grammar errors
• Improve sentence structure  
• Suggest better word choices
• Explain the corrections

💡 *Example:* "I are going to school yesterday"

📤 Just type your text and I'll help you improve it!

_Type *menu* to change modes_""",

        "chat": """💬 *General Chat Mode Activated!*

🌍 Let's have a friendly conversation!

• Talk in English, Kannada, or Telugu
• Ask me anything - I'm here to help  
• Share your thoughts, ask questions
• I'll remember our conversation context

😊 What's on your mind today?

_Type *menu* to change modes_""",

        "vocabulary": """📚 *Vocabulary Learning Mode Activated!*

🎯 I'll help you expand your vocabulary:

• Ask for word meanings and examples
• Learn synonyms and antonyms
• Practice using words in sentences
• Get pronunciation tips

💡 *Try asking:*
"What does 'serendipity' mean?"
"Give me 5 words for 'happy'"

_Type *menu* to change modes_""",

        "dreams": """🌙 *Dream Journal Mode Activated!*

✨ Share your dreams and I'll provide:

• Psychological interpretations
• Symbolic meaning analysis
• Emotional insights
• Pattern recognition across dreams

💭 *Just describe your dream:*
"I dreamed I was flying over a city..."

🔒 Your dreams are private and safe with me.

_Type *menu* to change modes_""",

        "practice": """🎓 *Language Practice Mode Activated!*

📖 Structured learning activities:

• Grammar exercises with explanations
• Sentence construction practice
• Translation challenges
• Pronunciation guidance

🎯 *Try asking:*
"Give me a grammar exercise"
"How to pronounce 'entrepreneur'?"

_Type *menu* to change modes_"""
    }
    
    return mode_messages.get(mode, "Mode activated! Type *menu* to return to main menu.")


def handle_whatsapp_command(message: str, phone_number: str) -> str:
    """Handle WhatsApp commands and mode selection"""
    message_lower = message.lower().strip()
    
    # Handle menu command
    if message_lower in ["menu", "/menu", "start", "/start"]:
        set_whatsapp_user_mode(phone_number, "menu")
        return create_whatsapp_menu_message()
    
    # Handle mode selection by number
    mode_map = {
        "1": "grammar",
        "2": "chat", 
        "3": "vocabulary",
        "4": "dreams",
        "5": "practice"
    }
    
    if message_lower in mode_map:
        mode = mode_map[message_lower]
        set_whatsapp_user_mode(phone_number, mode)
        return create_mode_activation_message(mode)
    
    # Handle mode selection by keyword
    keyword_map = {
        "grammar": "grammar",
        "chat": "chat",
        "vocab": "vocabulary",
        "vocabulary": "vocabulary",
        "dreams": "dreams",
        "dream": "dreams",
        "practice": "practice",
        "exercise": "practice"
    }
    
    if message_lower in keyword_map:
        mode = keyword_map[message_lower]
        set_whatsapp_user_mode(phone_number, mode)
        return create_mode_activation_message(mode)
    
    return None  # Not a command, process as regular message


def handle_interactive_response(button_payload: str = None, list_reply: str = None, phone_number: str = "") -> str:
    """Handle responses from interactive buttons/lists"""
    
    # Handle button responses
    if button_payload:
        try:
            payload_data = json.loads(button_payload)
            button_id = payload_data.get("id", "")
            
            if button_id == "back_to_menu":
                set_whatsapp_user_mode(phone_number, "menu")
                return "show_menu"
                
        except json.JSONDecodeError:
            logger.error(f"Invalid button payload: {button_payload}")
    
    # Handle list responses  
    if list_reply:
        try:
            list_data = json.loads(list_reply)
            selected_id = list_data.get("id", "")
            
            if selected_id.startswith("mode_"):
                mode = selected_id.replace("mode_", "")
                set_whatsapp_user_mode(phone_number, mode)
                return create_mode_activation_message(mode)
                
        except json.JSONDecodeError:
            logger.error(f"Invalid list reply: {list_reply}")
    
    return None





async def download_voice_message(media_url: str, twilio_client: Client) -> bytes:
    """Download voice message from Twilio"""
    try:
        # Get Twilio credentials for authentication
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        # Create basic auth header
        auth_string = f"{account_sid}:{auth_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Authorization": f"Basic {auth_b64}"
        }
        
        # Configure client to follow redirects
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            # First request to get the redirect URL
            response = await client.get(media_url, headers=headers)
            
            if response.status_code == 307:
                # Handle redirect manually if needed
                redirect_url = response.headers.get('location')
                if redirect_url:
                    logger.info(f"Following redirect to: {redirect_url}")
                    # Download from the redirected URL (no auth needed for CDN)
                    response = await client.get(redirect_url)
            
            response.raise_for_status()
            return response.content
            
    except Exception as e:
        logger.error(f"Error downloading voice message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download voice message: {str(e)}"
        )


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    ProfileName: Optional[str] = Form(None),
    MessageSid: Optional[str] = Form(None),
    NumMedia: Optional[str] = Form(None),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None),
    ButtonPayload: Optional[str] = Form(None),
    ListReply: Optional[str] = Form(None)
):
    """
    Webhook endpoint for receiving WhatsApp messages via Twilio
    
    Twilio sends POST requests with form data when messages are received
    Supports both text messages and voice messages
    """
    try:
        # Determine message type
        num_media = int(NumMedia or "0")
        is_voice_message = (
            num_media > 0 and 
            MediaContentType0 and 
            MediaContentType0.startswith("audio/")
        )
        
        if is_voice_message:
            logger.info(f"Received WhatsApp voice message from {From}")
            message_content = "🎤 Voice message received"
            message_type = "voice"
        else:
            logger.info(f"Received WhatsApp text message from {From}: {Body}")
            message_content = Body or ""
            message_type = "text"
        
        # Extract phone number (remove 'whatsapp:' prefix)
        phone_number = From.replace('whatsapp:', '')
        user_name = ProfileName or phone_number
        
        # Handle interactive responses first
        interactive_response = handle_interactive_response(ButtonPayload, ListReply, phone_number)
        if interactive_response:
            if interactive_response == "show_menu":
                # Send interactive menu
                success = await send_interactive_menu(phone_number)
                if success:
                    # Return empty TwiML since we sent via API
                    twiml_response = MessagingResponse()
                    from fastapi import Response
                    return Response(content=str(twiml_response), media_type="application/xml")
                else:
                    # Fallback to text menu
                    response_text = create_whatsapp_menu_message()
            else:
                # Mode activation message
                response_text = interactive_response
                
            # Create TwiML response
            twiml_response = MessagingResponse()
            twiml_response.message(response_text)
            
            from fastapi import Response
            return Response(content=str(twiml_response), media_type="application/xml")
        
        # Get conversation service
        conv_service = get_conversation_service()
        
        # Handle voice messages
        if is_voice_message:
            try:
                logger.info(f"Processing voice message from {phone_number}")
                
                # Download the voice message
                twilio_client = get_twilio_client()
                voice_data = await download_voice_message(MediaUrl0, twilio_client)
                
                # Convert voice to text using STT service
                stt = get_stt_service()
                
                # Save voice data to temporary file
                with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                    temp_file.write(voice_data)
                    temp_file_path = temp_file.name
                
                try:
                    # Transcribe voice to text
                    transcription = await stt.transcribe_audio(temp_file_path)
                    
                    if transcription and transcription.strip():
                        logger.info(f"Voice transcription: {transcription}")
                        message_content = transcription
                        
                        # Process the transcribed text with AI
                        request = ConversationRequest(
                            user_id=phone_number,
                            user_name=user_name,
                            message=message_content,
                            interface="whatsapp",
                            conversation_id=None,
                            message_type="voice"
                        )
                        
                        response = await conv_service.process_message(request)
                        response_text = f"🎤 I heard you say: \"{transcription}\"\n\n{response.response_text}"
                    else:
                        response_text = (
                            "🎤 I received your voice message but couldn't understand what you said. "
                            "Could you please try again or send me a text message? 😊"
                        )
                        
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                        
            except Exception as e:
                logger.error(f"Error processing voice message: {e}")
                response_text = (
                    "🎤 I received your voice message but had trouble processing it. "
                    "Please try sending a text message instead, and I'll be happy to help! 😊"
                )
        else:
            # Process text message normally
            if not message_content.strip():
                response_text = "I didn't receive any text in your message. Please send me a text message and I'll be happy to help! 😊"
            else:
                # Check if it's a command or mode selection
                command_response = handle_whatsapp_command(message_content, phone_number)
                
                if command_response:
                    # Check if it's a menu request
                    if "Choose what you'd like to do" in command_response:
                        # Try to send interactive menu
                        success = await send_interactive_menu(phone_number)
                        if success:
                            # Return empty TwiML since we sent via API
                            twiml_response = MessagingResponse()
                            from fastapi import Response
                            return Response(content=str(twiml_response), media_type="application/xml")
                        else:
                            # Fallback to text menu
                            response_text = command_response
                    else:
                        # Check if it's a mode activation
                        mode_activated = None
                        for mode in ["grammar", "chat", "vocabulary", "dreams", "practice"]:
                            if f"{mode.title()} Mode Activated" in command_response:
                                mode_activated = mode
                                break
                        
                        if mode_activated:
                            # Try to send with interactive button
                            success = await send_mode_activation_with_button(phone_number, mode_activated)
                            if success:
                                # Return empty TwiML since we sent via API
                                twiml_response = MessagingResponse()
                                from fastapi import Response
                                return Response(content=str(twiml_response), media_type="application/xml")
                        
                        # Fallback to text response
                        response_text = command_response
                else:
                    # Regular message - process based on current mode
                    session = get_whatsapp_user_session(phone_number)
                    current_mode = session.get("mode", "menu")
                    
                    if current_mode == "menu":
                        # User is in menu mode but didn't select a valid option
                        # Try to send interactive menu
                        success = await send_interactive_menu(phone_number)
                        if success:
                            # Return empty TwiML since we sent via API
                            twiml_response = MessagingResponse()
                            from fastapi import Response
                            return Response(content=str(twiml_response), media_type="application/xml")
                        else:
                            # Fallback to text menu
                            response_text = create_whatsapp_menu_message()
                    else:
                        # Process message in the selected mode
                        request = ConversationRequest(
                            user_id=phone_number,
                            user_name=user_name,
                            message=message_content,
                            interface="whatsapp",
                            conversation_id=None,
                            message_type=message_type,
                            mode_context=current_mode
                        )
                        
                        # Process message and get response
                        response = await conv_service.process_message(request)
                        
                        # Add mode indicator and menu option
                        mode_emoji = {
                            "grammar": "✏️",
                            "chat": "💬", 
                            "vocabulary": "📚",
                            "dreams": "🌙",
                            "practice": "🎓"
                        }
                        
                        emoji = mode_emoji.get(current_mode, "💬")
                        message_text = f"{emoji} {response.response_text}"
                        
                        # Try to send with back button
                        back_button = [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "back_to_menu",
                                    "title": "🔙 Back to Menu"
                                }
                            }
                        ]
                        
                        success = await send_interactive_buttons(phone_number, message_text, back_button)
                        if success:
                            # Return empty TwiML since we sent via API
                            twiml_response = MessagingResponse()
                            from fastapi import Response
                            return Response(content=str(twiml_response), media_type="application/xml")
                        else:
                            # Fallback to text with visual button
                            response_text = f"{message_text}\n\n_Type *menu* to change modes_"
        
        # Create Twilio response
        twiml_response = MessagingResponse()
        twiml_response.message(response_text)
        
        # Log the response being sent
        logger.info(f"Sending WhatsApp response to {phone_number}: {response_text[:100]}...")
        logger.info(f"TwiML Response: {str(twiml_response)}")
        
        # Return TwiML with proper content type
        from fastapi import Response
        return Response(
            content=str(twiml_response),
            media_type="application/xml"
        )
    
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}", exc_info=True)
        
        # Send error message to user
        twiml_response = MessagingResponse()
        twiml_response.message("Sorry, I encountered an error. Please try again later.")
        
        # Return TwiML with proper content type
        from fastapi import Response
        return Response(
            content=str(twiml_response),
            media_type="application/xml"
        )


@router.get("/status")
async def whatsapp_status():
    """Check WhatsApp integration status"""
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([account_sid, auth_token, phone_number]):
            return {
                "status": "not_configured",
                "message": "Twilio credentials not configured in .env file"
            }
        
        # Try to get Twilio client
        client = get_twilio_client()
        
        # Get account info
        account = client.api.accounts(account_sid).fetch()
        
        return {
            "status": "configured",
            "account_status": account.status,
            "phone_number": phone_number,
            "message": "WhatsApp integration is ready"
        }
    
    except Exception as e:
        logger.error(f"Error checking WhatsApp status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
