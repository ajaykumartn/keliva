"""
WhatsApp Integration via Make.com
Enhanced WhatsApp integration using Make.com for better interactive message support
"""
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
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

router = APIRouter(prefix="/api/whatsapp-makecom", tags=["whatsapp-makecom"])

# Initialize services
conversation_service = None
db_manager = None

# User session storage (in production, use Redis or database)
whatsapp_user_sessions = {}


class WhatsAppIncomingMessage(BaseModel):
    """Model for incoming WhatsApp messages from Make.com"""
    phone_number: str
    message: Optional[str] = None
    message_type: str = "text"  # text, voice, image, document, button, list
    user_name: Optional[str] = None
    media_url: Optional[str] = None
    button_payload: Optional[str] = None
    list_reply: Optional[str] = None
    timestamp: Optional[str] = None


class WhatsAppOutgoingM