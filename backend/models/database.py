"""
Database models and Pydantic schemas for KeLiva
Supports both Cloudflare D1 (SQLite) and local SQLite development
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import json


# Enums
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    GRAMMAR_CHECK = "grammar_check"


class InterfaceType(str, Enum):
    WEB = "web"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"


class Language(str, Enum):
    ENGLISH = "en"
    KANNADA = "kn"
    TELUGU = "te"


# Pydantic Models for API requests/responses
class UserBase(BaseModel):
    name: Optional[str] = None
    telegram_id: Optional[int] = None
    session_id: Optional[str] = None  # For web users
    preferred_language: str = "en"


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: str
    created_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    user_id: str
    interface: str = "telegram"


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    conversation_id: str
    role: str
    content: str
    language: str = "en"
    message_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class GrammarError(BaseModel):
    start_pos: int
    end_pos: int
    error_type: str
    original_text: str
    corrected_text: str
    explanation: str
    severity: str = "moderate"


class GrammarCorrectionBase(BaseModel):
    message_id: str
    original_text: str
    corrected_text: str
    errors: List[GrammarError] = []


class GrammarCorrectionCreate(GrammarCorrectionBase):
    pass


class GrammarCorrection(GrammarCorrectionBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class UserFactBase(BaseModel):
    user_id: str
    fact_text: str
    category: Optional[str] = None


class UserFactCreate(UserFactBase):
    pass


class UserFact(UserFactBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
