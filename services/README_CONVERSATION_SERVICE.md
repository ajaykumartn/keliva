# Conversation Service

The Conversation Service is the core orchestrator for KeLiva's conversation flow. It integrates all components (language detection, knowledge vault, persona system) to provide a seamless conversational experience.

## Overview

The Conversation Service implements the complete text message processing pipeline:

```
User Input → Language Detection → Context Retrieval → LLM Response → Message Storage
```

## Features

- **Language Detection**: Automatically detects English, Kannada, or Telugu
- **Language Mirroring**: Responds in the same language as the user input
- **Context-Aware Responses**: Retrieves relevant facts from Knowledge Vault
- **Fact Extraction**: Automatically extracts and stores personal information
- **Conversation History**: Maintains conversation context across sessions
- **Cross-Platform**: Works with Telegram, WhatsApp, and web interfaces
- **Message Persistence**: Stores all messages with proper metadata

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Conversation Service                        │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  Polyglot  │  │ Knowledge  │  │    Vani    │       │
│  │   Engine   │  │   Vault    │  │  Persona   │       │
│  └────────────┘  └────────────┘  └────────────┘       │
│                                                          │
│  ┌────────────────────────────────────────────┐        │
│  │         Database Manager                    │        │
│  │  (Conversations, Messages, Users)           │        │
│  └────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

## Usage

### Basic Example

```python
from services.conversation_service import ConversationService, ConversationRequest
from utils.db_manager import DatabaseManager

# Initialize
db_manager = DatabaseManager(db_path="keliva.db")
conversation_service = ConversationService(
    db_manager=db_manager,
    chroma_persist_dir="./chroma_db"
)

# Get or create user
user_id = await conversation_service.get_or_create_user(
    telegram_id=123456789,
    name="User Name",
    preferred_language="en"
)

# Process a message
request = ConversationRequest(
    user_id=user_id,
    user_name="User Name",
    message="Hi! I'm feeling stressed about my exams.",
    interface="telegram",
    message_type="text"
)

response = await conversation_service.process_message(request)

print(f"Response: {response.response_text}")
print(f"Language: {response.language.value}")
print(f"Facts extracted: {response.facts_extracted}")
```

### Continue a Conversation

```python
# Continue the same conversation
request2 = ConversationRequest(
    user_id=user_id,
    user_name="User Name",
    message="My friend Abhishek is helping me study.",
    interface="telegram",
    conversation_id=response.conversation_id,  # Same conversation
    message_type="text"
)

response2 = await conversation_service.process_message(request2)
```

### Get Conversation History

```python
# Get conversation history for display
history = conversation_service.get_conversation_history_for_user(
    user_id=user_id,
    conversation_id=response.conversation_id,
    limit=50
)

for msg in history:
    print(f"{msg['role']}: {msg['content']}")
```

### Get User Context Summary

```python
# Get summary of stored facts about the user
context = await conversation_service.get_user_context_summary(user_id)

print(f"Total facts: {context['total_facts']}")
print(f"Entities: {list(context['entities'].keys())}")
```

## API Reference

### ConversationService

#### `__init__(db_manager, api_key=None, chroma_persist_dir="./chroma_db")`

Initialize the conversation service.

**Parameters:**
- `db_manager` (DatabaseManager): Database manager instance
- `api_key` (str, optional): Groq API key (defaults to GROQ_API_KEY env var)
- `chroma_persist_dir` (str): Directory for ChromaDB persistence

#### `async process_message(request: ConversationRequest) -> ConversationResponse`

Processes a user message through the complete conversation pipeline.

**Parameters:**
- `request` (ConversationRequest): Request with user message and metadata

**Returns:**
- `ConversationResponse`: Response with generated text and metadata

**Pipeline Steps:**
1. Detect language of input
2. Get or create conversation
3. Retrieve conversation history
4. Extract and store facts from user message
5. Retrieve relevant context from Knowledge Vault
6. Generate response using Vani persona
7. Store user message and assistant response
8. Return response

#### `async get_or_create_user(telegram_id=None, name=None, preferred_language="en") -> str`

Gets existing user or creates a new one.

**Parameters:**
- `telegram_id` (int, optional): Telegram user ID
- `name` (str, optional): User name
- `preferred_language` (str): Preferred language code (default: "en")

**Returns:**
- `str`: User ID

#### `get_conversation_history_for_user(user_id, conversation_id=None, limit=50) -> List[Dict]`

Retrieves conversation history for display to user.

**Parameters:**
- `user_id` (str): User identifier
- `conversation_id` (str, optional): Specific conversation ID
- `limit` (int): Maximum number of messages (default: 50)

**Returns:**
- `List[Dict]`: List of message dictionaries with full details

#### `async get_user_context_summary(user_id, query=None) -> Dict`

Gets a summary of stored context for a user.

**Parameters:**
- `user_id` (str): User identifier
- `query` (str, optional): Query to filter relevant facts

**Returns:**
- `Dict`: Dictionary with context summary including entities and facts

#### `end_conversation(conversation_id: str) -> None`

Marks a conversation as ended.

**Parameters:**
- `conversation_id` (str): Conversation identifier

### Data Classes

#### ConversationRequest

```python
@dataclass
class ConversationRequest:
    user_id: str
    user_name: str
    message: str
    interface: str = "telegram"  # "telegram", "whatsapp", or "web"
    conversation_id: Optional[str] = None
    message_type: str = "text"  # "text" or "voice"
```

#### ConversationResponse

```python
@dataclass
class ConversationResponse:
    response_text: str
    language: Language
    conversation_id: str
    message_id: str
    emotional_tone: EmotionalTone
    facts_extracted: int
    concealment_applied: bool
```

## Integration Examples

### Telegram Bot Integration

```python
from telegram import Update
from telegram.ext import ContextTypes

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get user info
    telegram_id = update.effective_user.id
    user_name = update.effective_user.first_name
    message_text = update.message.text
    
    # Get or create user
    user_id = await conversation_service.get_or_create_user(
        telegram_id=telegram_id,
        name=user_name
    )
    
    # Process message
    request = ConversationRequest(
        user_id=user_id,
        user_name=user_name,
        message=message_text,
        interface="telegram"
    )
    
    response = await conversation_service.process_message(request)
    
    # Send response
    await update.message.reply_text(response.response_text)
```

### REST API Integration

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    user_name: str
    message: str
    conversation_id: Optional[str] = None

@router.post("/api/chat/message")
async def chat_message(request: ChatRequest):
    try:
        conv_request = ConversationRequest(
            user_id=request.user_id,
            user_name=request.user_name,
            message=request.message,
            interface="web",
            conversation_id=request.conversation_id
        )
        
        response = await conversation_service.process_message(conv_request)
        
        return {
            "response": response.response_text,
            "language": response.language.value,
            "conversation_id": response.conversation_id,
            "emotional_tone": response.emotional_tone.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Language Mirroring

The service automatically detects the language of user input and responds in the same language:

- **English input** → English response (with grammar correction mode)
- **Kannada input** → Kannada response (comfort mode)
- **Telugu input** → Telugu response (comfort mode)

Example:
```python
# English
request = ConversationRequest(message="I am feeling stressed")
response = await service.process_message(request)
# response.language == Language.ENGLISH

# Kannada
request = ConversationRequest(message="ನಾನು ತುಂಬಾ ಖುಷಿಯಾಗಿದ್ದೇನೆ")
response = await service.process_message(request)
# response.language == Language.KANNADA
```

## Fact Extraction and Context

The service automatically:
1. Extracts facts from user messages (names, relationships, events)
2. Stores facts in the Knowledge Vault
3. Retrieves relevant facts before generating responses
4. Incorporates facts into the persona prompt for context-aware replies

Example:
```python
# First message
request1 = ConversationRequest(message="My friend Abhishek helps me with robotics")
response1 = await service.process_message(request1)
# Facts extracted: "Abhishek", "friend", "robotics"

# Later message
request2 = ConversationRequest(message="Tell me about Abhishek")
response2 = await service.process_message(request2)
# Response will mention: "Abhishek is your friend who helps with robotics"
```

## Error Handling

The service includes comprehensive error handling:

- **API failures**: Falls back to friendly default responses
- **Database errors**: Logs errors but continues processing
- **Invalid input**: Handles empty messages gracefully
- **Missing context**: Works without conversation history

## Performance

- **Language detection**: ~100-200ms (LLM-based)
- **Fact extraction**: ~500-1000ms (LLM-based)
- **Context retrieval**: ~50-100ms (vector search)
- **Response generation**: ~500-1500ms (LLM-based)
- **Total latency**: ~1-3 seconds per message

## Testing

Run the test suite:

```bash
cd backend
python test_conversation_service.py
```

Run the example:

```bash
cd backend
python example_conversation_usage.py
```

## Requirements

- Python 3.11+
- Groq API key (FREE - 14,000 requests/day)
- SQLite or PostgreSQL database
- ChromaDB for vector storage

## Dependencies

```
groq
chromadb
sentence-transformers
pydantic
python-dotenv
```

## See Also

- [Polyglot Engine](README_POLYGLOT_ENGINE.md) - Language detection
- [Knowledge Vault](README_KNOWLEDGE_VAULT.md) - Context storage
- [Vani Persona](README_VANI_PERSONA.md) - Response generation
- [Grammar Guardian](README_GRAMMAR_GUARDIAN.md) - Grammar correction
