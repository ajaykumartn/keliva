"""
Telegram Bot API integration
Provides webhook endpoint for receiving messages from Telegram
100% FREE - No rate limits for personal use
"""
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
import hmac
import hashlib
import httpx
import logging
import json

from services.conversation_service import (
    ConversationService,
    ConversationRequest
)
from utils.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])

# Initialize services
conversation_service = None
db_manager = None

# User session storage (in production, use Redis or database)
user_sessions = {}


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


# Telegram webhook models
class TelegramUser(BaseModel):
    """Telegram user information"""
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramChat(BaseModel):
    """Telegram chat information"""
    id: int
    type: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class TelegramMessage(BaseModel):
    """Telegram message structure"""
    message_id: int
    from_: TelegramUser = Field(..., alias="from")
    chat: TelegramChat
    date: int
    text: Optional[str] = None
    voice: Optional[Dict[str, Any]] = None


class TelegramCallbackQuery(BaseModel):
    """Telegram callback query from inline keyboard"""
    id: str
    from_: TelegramUser = Field(..., alias="from")
    message: Optional[TelegramMessage] = None
    data: Optional[str] = None


class TelegramUpdate(BaseModel):
    """Telegram webhook update"""
    update_id: int
    message: Optional[TelegramMessage] = None
    callback_query: Optional[TelegramCallbackQuery] = None


class TelegramBotAPI:
    """Helper class for Telegram Bot API operations"""
    
    def __init__(self, bot_token: str):
        """
        Initialize Telegram Bot API client.
        
        Args:
            bot_token: Telegram bot token from @BotFather
        """
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a text message to a Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text to send
            parse_mode: Optional parse mode (Markdown, HTML)
            
        Returns:
            API response dictionary
            
        Raises:
            HTTPException: If message sending fails
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
            
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send message: {str(e)}"
            )
    
    async def set_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """
        Set the webhook URL for receiving updates.
        
        Args:
            webhook_url: HTTPS URL for webhook
            
        Returns:
            API response dictionary
        """
        url = f"{self.base_url}/setWebhook"
        payload = {"url": webhook_url}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to set webhook: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to set webhook: {str(e)}"
            )
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """
        Get current webhook status.
        
        Returns:
            Webhook information dictionary
        """
        url = f"{self.base_url}/getWebhookInfo"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get webhook info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get webhook info: {str(e)}"
            )
    
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> Dict[str, Any]:
        """
        Answer a callback query from inline keyboard.
        
        Args:
            callback_query_id: Callback query ID
            text: Optional notification text
            show_alert: Whether to show as alert or notification
            
        Returns:
            API response dictionary
        """
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        
        if text:
            payload["text"] = text
        if show_alert:
            payload["show_alert"] = show_alert
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to answer callback query: {e}")
            # Don't raise exception for callback query errors - just log them
            return {"ok": False, "error": str(e)}


def get_user_session(user_id: int) -> Dict[str, Any]:
    """Get or create user session"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "mode": "menu",  # menu, grammar, chat, vocabulary, dreams
            "language": "en",
            "conversation_history": []
        }
    return user_sessions[user_id]

def set_user_mode(user_id: int, mode: str):
    """Set user's current mode"""
    session = get_user_session(user_id)
    session["mode"] = mode
    user_sessions[user_id] = session

def verify_telegram_webhook(request: Request, bot_token: str) -> bool:
    """
    Verify that the webhook request is from Telegram.
    
    Uses the X-Telegram-Bot-Api-Secret-Token header if set,
    or validates the request structure.
    
    Args:
        request: FastAPI request object
        bot_token: Telegram bot token
        
    Returns:
        True if request is valid, False otherwise
    """
    # Check for secret token header (if configured)
    secret_token = os.getenv("TELEGRAM_SECRET_TOKEN")
    if secret_token:
        request_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if request_token != secret_token:
            logger.warning("Invalid Telegram secret token")
            return False
    
    # Additional validation can be added here
    # For now, we rely on HTTPS and secret token
    return True


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Webhook endpoint for receiving Telegram updates.
    
    This endpoint receives messages from Telegram Bot API and processes them
    through the conversation service. Supports:
    - Text messages
    - Commands (/start, /help)
    - Voice notes (directs users to web interface)
    
    The webhook must be configured via Telegram Bot API:
    POST https://api.telegram.org/bot<TOKEN>/setWebhook
    {
        "url": "https://your-domain.com/api/telegram/webhook",
        "secret_token": "your-secret-token"
    }
    
    Returns:
        Success response for Telegram API
        
    Raises:
        HTTPException: If webhook validation fails or processing errors occur
    """
    # Get bot token
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram bot not configured"
        )
    
    # Verify webhook authenticity
    if not verify_telegram_webhook(request, bot_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook request"
        )
    
    # Parse webhook payload
    try:
        body = await request.json()
        update = TelegramUpdate(**body)
    except Exception as e:
        logger.error(f"Failed to parse Telegram update: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid update format: {str(e)}"
        )
    
    # Initialize Telegram Bot API client
    bot_api = TelegramBotAPI(bot_token)
    
    # Handle callback queries (button clicks)
    if update.callback_query:
        await handle_callback_query(update.callback_query, bot_api)
        return {"ok": True}
    
    # Check if update contains a message
    if not update.message:
        logger.info("Update does not contain a message, ignoring")
        return {"ok": True}
    
    message = update.message
    telegram_user = message.from_
    chat_id = message.chat.id
    
    try:
        # Handle voice notes
        if message.voice:
            await process_voice_message(message, telegram_user, bot_api)
            return {"ok": True}
        
        # Check if message has text
        if not message.text:
            logger.info("Message has no text content, ignoring")
            return {"ok": True}
        
        # Handle commands
        if message.text.startswith("/"):
            await handle_command(message.text, chat_id, telegram_user, bot_api)
            return {"ok": True}
        
        # Handle number selections (1-5)
        if message.text.strip() in ["1", "2", "3", "4", "5"]:
            await handle_number_selection(message.text.strip(), chat_id, telegram_user, bot_api)
            return {"ok": True}
        
        # Process regular text message based on current mode
        await process_text_message(message, telegram_user, bot_api)
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error processing Telegram message: {e}")
        # Send error message to user
        try:
            error_text = (
                "😔 Sorry, I encountered an error processing your message.\n"
                "Please try again in a moment."
            )
            await bot_api.send_message(chat_id, error_text)
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")
        
        # Return success to Telegram to avoid retries
        return {"ok": True}


async def handle_callback_query(
    callback_query: TelegramCallbackQuery,
    bot_api: TelegramBotAPI
):
    """Handle callback queries from inline keyboard buttons"""
    user = callback_query.from_
    chat_id = callback_query.message.chat.id if callback_query.message else user.id
    data = callback_query.data
    
    try:
        # Answer the callback query to remove loading state
        await bot_api.answer_callback_query(callback_query.id)
        
        if data == "back_to_menu":
            # Show main menu
            set_user_mode(user.id, "menu")
            await show_main_menu(chat_id, user, bot_api)
        elif data.startswith("mode_"):
            # Handle mode selection
            mode = data.replace("mode_", "")
            await handle_mode_selection(mode, chat_id, user, bot_api)
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        # Continue processing even if callback answer fails


async def handle_mode_selection(
    mode: str,
    chat_id: int,
    user: TelegramUser,
    bot_api: TelegramBotAPI
):
    """Handle mode selection from inline keyboard"""
    set_user_mode(user.id, mode)
    
    mode_messages = {
        "grammar": {
            "text": "✏️ *Grammar Check Mode Activated!*\n\n"
                   "📝 Send me any English text and I'll:\n"
                   "• Fix grammar errors\n"
                   "• Improve sentence structure\n"
                   "• Suggest better word choices\n"
                   "• Explain the corrections\n\n"
                   "💡 *Example:* \"I are going to school yesterday\"\n"
                   "📤 Just type your text and I'll help you improve it!",
            "emoji": "✏️"
        },
        "chat": {
            "text": "💬 *General Chat Mode Activated!*\n\n"
                   "🌍 Let's have a friendly conversation!\n"
                   "• Talk in English, Kannada, or Telugu\n"
                   "• Ask me anything - I'm here to help\n"
                   "• Share your thoughts, ask questions\n"
                   "• I'll remember our conversation context\n\n"
                   "😊 What's on your mind today?",
            "emoji": "💬"
        },
        "vocabulary": {
            "text": "📚 *Vocabulary Learning Mode Activated!*\n\n"
                   "🎯 I'll help you expand your vocabulary:\n"
                   "• Ask for word meanings and examples\n"
                   "• Learn synonyms and antonyms\n"
                   "• Practice using words in sentences\n"
                   "• Get pronunciation tips\n\n"
                   "💡 *Try asking:*\n"
                   "\"What does 'serendipity' mean?\"\n"
                   "\"Give me 5 words for 'happy'\"",
            "emoji": "📚"
        },
        "dreams": {
            "text": "🌙 *Dream Journal Mode Activated!*\n\n"
                   "✨ Share your dreams and I'll provide:\n"
                   "• Psychological interpretations\n"
                   "• Symbolic meaning analysis\n"
                   "• Emotional insights\n"
                   "• Pattern recognition across dreams\n\n"
                   "💭 *Just describe your dream:*\n"
                   "\"I dreamed I was flying over a city...\"\n\n"
                   "🔒 Your dreams are private and safe with me.",
            "emoji": "🌙"
        },
        "practice": {
            "text": "🎓 *Language Practice Mode Activated!*\n\n"
                   "📖 Structured learning activities:\n"
                   "• Grammar exercises with explanations\n"
                   "• Sentence construction practice\n"
                   "• Translation challenges\n"
                   "• Pronunciation guidance\n\n"
                   "🎯 *Try asking:*\n"
                   "\"Give me a grammar exercise\"\n"
                   "\"How to pronounce 'entrepreneur'?\"",
            "emoji": "🎓"
        }
    }
    
    if mode in mode_messages:
        message_data = mode_messages[mode]
        await bot_api.send_message(
            chat_id,
            message_data["text"],
            parse_mode="Markdown",
            reply_markup=create_back_to_menu_keyboard()
        )


async def show_main_menu(
    chat_id: int,
    user: TelegramUser,
    bot_api: TelegramBotAPI
):
    """Show the main menu with inline keyboard"""
    welcome_text = (
        f"👋 Hello {user.first_name}! I'm Captain, your AI companion.\n\n"
        "🎯 *Choose what you'd like to do:*"
    )
    
    await bot_api.send_message(
        chat_id,
        welcome_text,
        parse_mode="Markdown",
        reply_markup=create_main_menu_keyboard()
    )


async def handle_number_selection(
    number: str,
    chat_id: int,
    user: TelegramUser,
    bot_api: TelegramBotAPI
):
    """Handle number selection (1-5) for mode switching - kept for backward compatibility"""
    mode_map = {
        "1": "grammar",
        "2": "chat", 
        "3": "vocabulary",
        "4": "dreams",
        "5": "practice"
    }
    
    if number in mode_map:
        await handle_mode_selection(mode_map[number], chat_id, user, bot_api)

async def handle_command(
    command: str,
    chat_id: int,
    user: TelegramUser,
    bot_api: TelegramBotAPI
):
    """
    Handle Telegram bot commands.
    
    Args:
        command: Command text (e.g., "/start", "/help")
        chat_id: Telegram chat ID
        user: Telegram user information
        bot_api: Telegram Bot API client
    """
    command_lower = command.lower().split()[0]
    
    if command_lower == "/start":
        # Reset user to menu mode
        set_user_mode(user.id, "menu")
        await show_main_menu(chat_id, user, bot_api)
    
    elif command_lower in ["/help", "/menu"]:
        set_user_mode(user.id, "menu")
        await show_main_menu(chat_id, user, bot_api)
    
    elif command_lower == "/grammar":
        await handle_mode_selection("grammar", chat_id, user, bot_api)
    
    elif command_lower == "/chat":
        await handle_mode_selection("chat", chat_id, user, bot_api)
    
    elif command_lower == "/vocab":
        await handle_mode_selection("vocabulary", chat_id, user, bot_api)
    
    elif command_lower == "/dreams":
        await handle_mode_selection("dreams", chat_id, user, bot_api)
    
    elif command_lower == "/practice":
        await handle_mode_selection("practice", chat_id, user, bot_api)
    
    else:
        unknown_text = (
            f"❓ Unknown command: {command}\n\n"
            "Type /help to see available commands."
        )
        await bot_api.send_message(chat_id, unknown_text)


async def process_text_message(
    message: TelegramMessage,
    user: TelegramUser,
    bot_api: TelegramBotAPI
):
    """
    Process a text message based on user's current mode.
    
    Args:
        message: Telegram message object
        user: Telegram user information
        bot_api: Telegram Bot API client
    """
    session = get_user_session(user.id)
    current_mode = session.get("mode", "menu")
    
    # If user is in menu mode, show menu with buttons
    if current_mode == "menu":
        await show_main_menu(message.chat.id, user, bot_api)
        return
    
    service = get_conversation_service()
    
    # Get or create user in database
    user_id = await service.get_or_create_user(
        telegram_id=user.id,
        session_id=None,
        name=user.first_name,
        preferred_language=user.language_code or "en"
    )
    
    # Create conversation request with mode context
    conv_request = ConversationRequest(
        user_id=user_id,
        user_name=user.first_name,
        message=message.text,  # Use original message, let persona handle mode-specific responses
        interface="telegram",
        message_type="text",
        mode_context=current_mode  # Pass the user's selected mode
    )
    
    # Process message through conversation pipeline
    response = await service.process_message(conv_request)
    
    # Add mode indicator to response
    mode_emoji = {
        "grammar": "✏️",
        "chat": "💬", 
        "vocabulary": "📚",
        "dreams": "🌙",
        "practice": "🎓"
    }
    
    emoji = mode_emoji.get(current_mode, "💬")
    formatted_response = f"{emoji} {response.response_text}"
    
    # Send response back to Telegram with back to menu button
    await bot_api.send_message(
        message.chat.id, 
        formatted_response, 
        parse_mode="Markdown",
        reply_markup=create_back_to_menu_keyboard()
    )
    
    logger.info(
        f"Processed {current_mode} message from {user.first_name} (ID: {user.id}), "
        f"language: {response.language.value}"
    )


async def process_voice_message(
    message: TelegramMessage,
    user: TelegramUser,
    bot_api: TelegramBotAPI
):
    """
    Process voice message from Telegram.
    
    Args:
        message: Telegram message with voice note
        user: Telegram user information
        bot_api: Telegram Bot API client
    """
    try:
        # Send "processing" message
        await bot_api.send_message(
            message.chat.id,
            "🎤 Processing your voice message..."
        )
        
        # For now, send a message that voice processing is not fully implemented
        # TODO: Implement actual voice-to-text conversion
        response_text = (
            "🎤 Voice message received!\n\n"
            "Voice processing is currently being implemented. "
            "For now, please send text messages and I'll respond right away!\n\n"
            "For full voice conversations, visit:\n"
            "👉 https://keliva-app.pages.dev"
        )
        
        await bot_api.send_message(message.chat.id, response_text)
        
    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await bot_api.send_message(
            message.chat.id,
            "😔 Sorry, I couldn't process your voice message. Please try sending a text message instead."
        )


@router.post("/set-webhook")
async def set_telegram_webhook(webhook_url: str):
    """
    Set the Telegram webhook URL.
    
    This is a helper endpoint for configuring the webhook.
    In production, you should set this via direct API call or Telegram Bot API.
    
    Args:
        webhook_url: HTTPS URL for webhook endpoint
        
    Returns:
        Webhook configuration result
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TELEGRAM_BOT_TOKEN not configured"
        )
    
    bot_api = TelegramBotAPI(bot_token)
    result = await bot_api.set_webhook(webhook_url)
    
    return {
        "message": "Webhook configured",
        "webhook_url": webhook_url,
        "result": result
    }


@router.get("/webhook-info")
async def get_telegram_webhook_info():
    """
    Get current Telegram webhook configuration.
    
    Returns:
        Current webhook information
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TELEGRAM_BOT_TOKEN not configured"
        )
    
    bot_api = TelegramBotAPI(bot_token)
    info = await bot_api.get_webhook_info()
    
    return info





def create_main_menu_keyboard() -> Dict[str, Any]:
    """Create the main menu inline keyboard"""
    return {
        "inline_keyboard": [
            [
                {"text": "✏️ Grammar Check", "callback_data": "mode_grammar"},
                {"text": "💬 General Chat", "callback_data": "mode_chat"}
            ],
            [
                {"text": "📚 Vocabulary", "callback_data": "mode_vocabulary"},
                {"text": "🌙 Dream Journal", "callback_data": "mode_dreams"}
            ],
            [
                {"text": "🎓 Language Practice", "callback_data": "mode_practice"}
            ],
            [
                {"text": "🎤 Voice Chat", "url": "https://keliva-app.pages.dev"}
            ]
        ]
    }


def create_back_to_menu_keyboard() -> Dict[str, Any]:
    """Create a simple back to menu keyboard"""
    return {
        "inline_keyboard": [
            [
                {"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}
            ]
        ]
    }
