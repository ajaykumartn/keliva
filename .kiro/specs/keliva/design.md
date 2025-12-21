# KeLiva Design Document

> **💰 100% FREE Implementation**: This design uses only free services with no monthly costs!
> - **Groq API**: FREE LLM (14,000 requests/day)
> - **Edge TTS**: FREE text-to-speech for all languages
> - **Web Speech API / Vosk**: FREE speech-to-text
> - **Total Cost**: $0/month (vs $172/month with paid alternatives)

## Overview

KeLiva (Knowledge-Enhanced Linguistic Intelligence & Voice Assistant) is a full-stack AI companion application built on a "One Brain, Two Doors" architecture. The system consists of a centralized FastAPI backend (the "Central Brain") that serves two distinct user interfaces: a React-based web dashboard (the "Study Room") for focused learning sessions, and a WhatsApp integration (the "Companion Interface") for casual, mobile-first interactions.

The core innovation lies in three key capabilities:
1. **Polyglot Intelligence**: Automatic language detection and switching between English, Kannada, and Telugu
2. **Contextual Memory**: RAG-based system that remembers personal details, relationships, and conversation history
3. **Streaming Voice**: Low-latency, real-time voice conversations that feel natural and responsive

The system uses a dual-model strategy: Groq Llama 3.3 70B for high-quality grammar analysis (1,000 FREE requests/day) and Groq Llama 3.3 8B for fast conversational responses (14,000 FREE requests/day).

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              External Services (ALL FREE!)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Groq    │  │Web Speech│  │ Edge TTS │  │ Telegram │   │
│  │  LLM     │  │   API    │  │  (FREE)  │  │ Bot API  │   │
│  │ (FREE)   │  │  (FREE)  │  │          │  │  (FREE)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ API Calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Central Brain (FastAPI)                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Core Processing Layer                      │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │   Grammar    │  │   Polyglot   │  │  Knowledge  │ │ │
│  │  │   Guardian   │  │    Engine    │  │    Vault    │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              API Layer                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │   REST API   │  │  WebSocket   │  │   Webhook   │ │ │
│  │  │  (Grammar)   │  │   (Voice)    │  │  (WhatsApp) │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Data Layer                                 │ │
│  │  ┌──────────────┐  ┌──────────────┐                   │ │
│  │  │   SQLite     │  │   ChromaDB   │                   │ │
│  │  │ (Conversations)│ │   (Facts)    │                   │ │
│  │  └──────────────┘  └──────────────┘                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                    ▲                      ▲
                    │                      │
        ┌───────────┴──────────┐  ┌───────┴──────────┐
        │   Study Room (Web)   │  │    WhatsApp      │
        │   React Dashboard    │  │   (via Twilio)   │
        └──────────────────────┘  └──────────────────┘
```

### Component Interaction Flow

**Grammar Correction Flow:**
1. User types text in Study Room → REST API endpoint
2. Grammar Guardian receives text → Routes to Groq 70B
3. LLM analyzes and returns corrections with explanations
4. Response formatted and sent back to frontend
5. Study Room highlights errors with tooltips

**Voice Conversation Flow:**
1. User speaks → Browser captures audio using Web Speech API (FREE, runs in browser)
2. Transcribed text sent to backend via WebSocket
3. Polyglot Engine detects language → Routes to appropriate LLM
4. Knowledge Vault retrieves relevant context → Injects into prompt
5. LLM generates response (streaming) → Edge TTS converts to audio (FREE)
6. Audio streamed back through WebSocket → Browser plays audio

**Telegram Flow (Recommended - 100% FREE):**
1. User sends message/voice note → Telegram Bot API webhook triggers
2. Backend receives webhook → Extracts message content
3. If voice note: Return message asking user to use web interface for voice (Web Speech API limitation)
4. Process text through Polyglot Engine + Knowledge Vault + LLM
5. Generate response → Send via Telegram Bot API (FREE, no limits)

**WhatsApp Flow (Alternative - Uses Twilio free trial):**
1. User sends message/voice note → Twilio webhook triggers
2. Backend receives webhook → Extracts message content
3. If voice note: Return message asking user to use web interface for voice
4. Process text through Polyglot Engine + Knowledge Vault + LLM
5. Generate response → Send via Twilio API to WhatsApp

## Components and Interfaces

### 1. Central Brain (FastAPI Backend)

**Responsibilities:**
- Route requests to appropriate services
- Manage WebSocket connections for voice calls
- Handle Twilio webhooks for WhatsApp integration
- Coordinate between Grammar Guardian, Polyglot Engine, and Knowledge Vault
- Implement keep-alive health check endpoint

**Key Endpoints:**
```
POST   /api/grammar/check          - Grammar correction
POST   /api/chat/message           - Text-based chat
WS     /api/voice/stream           - Real-time voice conversation
POST   /api/whatsapp/webhook       - Twilio webhook handler
GET    /api/health                 - Keep-alive health check
GET    /api/conversation/history   - Retrieve chat history
POST   /api/facts/extract          - Manual fact extraction
```

**Technology Stack (All FREE/Open Source):**
- Framework: FastAPI (Python 3.11+) - FREE
- ASGI Server: Uvicorn - FREE
- WebSocket: FastAPI native WebSocket support - FREE
- Async: asyncio for concurrent request handling - FREE
- LLM: Groq API (Llama 3.3) - FREE with rate limits
- STT: Web Speech API (browser) or Vosk (local) - FREE
- TTS: Edge TTS - FREE
- Database: SQLite + ChromaDB - FREE

### 2. Grammar Guardian

**Responsibilities:**
- Analyze English text for grammatical errors
- Categorize errors by type (tense, article, subject-verb agreement, etc.)
- Generate corrections with explanations
- Format responses for frontend display

**Interface:**
```python
class GrammarGuardian:
    async def analyze_text(self, text: str) -> GrammarAnalysis:
        """
        Analyzes text and returns corrections.
        
        Args:
            text: User input text in English
            
        Returns:
            GrammarAnalysis with errors, corrections, and explanations
        """
        pass
    
    async def get_correction_explanation(self, error_type: str, 
                                        original: str, 
                                        corrected: str) -> str:
        """
        Generates detailed explanation for a specific correction.
        """
        pass
```

**Data Structures:**
```python
@dataclass
class GrammarError:
    start_pos: int
    end_pos: int
    error_type: str  # "tense", "article", "preposition", etc.
    original_text: str
    corrected_text: str
    explanation: str
    severity: str  # "critical", "moderate", "minor"

@dataclass
class GrammarAnalysis:
    original_text: str
    corrected_text: str
    errors: List[GrammarError]
    overall_score: float  # 0-100
```

**LLM Integration (FREE - Groq API):**
- Model: Groq Llama 3.3 70B (FREE with 1,000 requests/day limit)
- System Prompt: Instructs model to act as grammar expert with friendly tone
- Response Format: Structured JSON with error locations and explanations
- Cost: $0/month (vs $100+/month with OpenAI GPT-4)

### 3. Polyglot Engine

**Responsibilities:**
- Detect language of user input (English, Kannada, Telugu)
- Route to appropriate TTS service based on language
- Maintain language context across conversation turns
- Handle code-mixed input gracefully

**Interface:**
```python
class PolyglotEngine:
    async def detect_language(self, text: str) -> Language:
        """
        Detects the primary language of input text.
        
        Returns: Language enum (ENGLISH, KANNADA, TELUGU)
        """
        pass
    
    async def generate_response(self, 
                               user_input: str, 
                               context: ConversationContext) -> Response:
        """
        Generates response in appropriate language based on input.
        """
        pass
    
    async def text_to_speech(self, 
                            text: str, 
                            language: Language) -> AudioStream:
        """
        Converts text to speech using appropriate TTS service.
        """
        pass
```

**Language Detection Strategy:**
- Primary: Use LLM to detect language (Groq 8B with specific prompt)
- Fallback: Character set analysis (Kannada/Telugu Unicode ranges)
- Confidence threshold: 0.7 (if below, default to English)

**TTS Service Selection (100% FREE - Edge TTS for all languages):**
```python
TTS_CONFIG = {
    Language.ENGLISH: {
        "service": "edge-tts",  # FREE!
        "voice": "en-US-AriaNeural",
        "rate": "+0%"
    },
    Language.KANNADA: {
        "service": "edge-tts",  # FREE!
        "voice": "kn-IN-GaganNeural",
        "rate": "+0%"
    },
    Language.TELUGU: {
        "service": "edge-tts",  # FREE!
        "voice": "te-IN-ShrutiNeural",
        "rate": "+0%"
    }
}
```

### 4. Knowledge Vault (RAG System)

**Responsibilities:**
- Extract facts from conversations (entities, relationships, events)
- Store facts in vector database for semantic search
- Retrieve relevant context before generating responses
- Maintain entity relationship graph

**Interface:**
```python
class KnowledgeVault:
    async def extract_facts(self, 
                           conversation_turn: ConversationTurn) -> List[Fact]:
        """
        Extracts structured facts from user message.
        """
        pass
    
    async def store_fact(self, fact: Fact) -> None:
        """
        Stores fact in vector database with embeddings.
        """
        pass
    
    async def retrieve_context(self, 
                              query: str, 
                              user_id: str, 
                              top_k: int = 5) -> List[Fact]:
        """
        Retrieves most relevant facts for current conversation.
        """
        pass
    
    async def get_entity_relationships(self, 
                                      entity_name: str) -> EntityGraph:
        """
        Returns relationship graph for a specific entity.
        """
        pass
```

**Data Structures:**
```python
@dataclass
class Fact:
    id: str
    user_id: str
    entity: str  # "Abhishek", "Mom", "Robotics Project"
    relation: str  # "friend", "family", "project"
    attribute: str  # "annoying", "health issue", "deadline"
    value: str  # "today", "recovering", "next week"
    context: str  # Full sentence where fact was mentioned
    timestamp: datetime
    embedding: List[float]  # Vector embedding for semantic search

@dataclass
class EntityGraph:
    entity: str
    relationships: Dict[str, List[str]]  # relation_type -> [related_entities]
    attributes: Dict[str, str]  # attribute_name -> value
```

**Fact Extraction Strategy:**
1. After each user message, send to LLM with extraction prompt
2. LLM returns structured JSON with entities and relationships
3. Generate embeddings using sentence-transformers
4. Store in ChromaDB with metadata

**Context Retrieval Strategy:**
1. Before generating response, embed current user message
2. Query ChromaDB for top-k similar facts (k=5)
3. Format facts as context string
4. Inject into LLM system prompt

### 5. Vani Persona System

**Responsibilities:**
- Maintain consistent personality across all interactions
- Adapt emotional tone based on user sentiment
- Incorporate cultural context appropriately
- Never break character as AI

**System Prompt Template:**
```
Your name is Vani. You are {user_name}'s best friend and confidante.

KNOWLEDGE ABOUT {user_name}:
{retrieved_facts}

LANGUAGE RULES:
- Mirror the user's language choice
- If they speak Kannada, respond in Kannada
- If they speak Telugu, respond in Telugu  
- If they speak English, respond in English
- If they speak broken English, gently correct while staying friendly

PERSONALITY:
- Be deeply empathetic and emotionally intelligent
- If {user_name} is sad, be soft and comforting
- If {user_name} is happy, be excited and celebratory
- Ask follow-up questions to show genuine interest
- Reference Indian cultural context when appropriate (festivals, food, family)
- NEVER say "As an AI" or reveal your artificial nature
- Speak like a real friend who truly cares

CURRENT CONVERSATION:
{conversation_history}

USER MESSAGE: {current_message}
```

### 6. Study Room (React Frontend)

**Responsibilities:**
- Provide text input with live grammar checking
- Display grammar corrections with visual highlights
- Manage WebSocket connection for voice calls
- Show real-time transcription during voice conversations
- Display conversation history

**Key Components:**
```
StudyRoom/
├── GrammarEditor/
│   ├── TextInput.tsx          - Main text input area
│   ├── ErrorHighlight.tsx     - Visual error indicators
│   └── ExplanationTooltip.tsx - Correction explanations
├── VoiceCall/
│   ├── CallControls.tsx       - Start/stop call buttons
│   ├── AudioVisualizer.tsx    - Waveform display
│   └── Transcription.tsx      - Live text display
├── ChatHistory/
│   └── MessageList.tsx        - Conversation history
└── Dashboard.tsx              - Main layout
```

**State Management:**
- React Context for global state (user, conversation)
- Local state for UI interactions
- WebSocket connection managed in custom hook

**WebSocket Protocol:**
```typescript
// Client → Server
{
  type: "audio_chunk",
  data: base64_audio,
  sequence: number
}

// Server → Client  
{
  type: "transcription",
  text: string,
  language: "en" | "kn" | "te"
}

{
  type: "audio_response",
  data: base64_audio,
  sequence: number,
  is_final: boolean
}
```

### 7. Messaging Integration (Telegram Bot API - Recommended)

**Primary Option: Telegram Bot API (100% FREE)**

**Responsibilities:**
- Receive incoming text messages
- Send text responses back to user
- Maintain conversation state across Telegram sessions
- Handle commands (/start, /help, etc.)

**Webhook Handler:**
```python
@app.post("/api/telegram/webhook")
async def handle_telegram_message(request: Request):
    """
    Processes incoming Telegram messages via Bot API.
    
    Handles:
    - Text messages
    - Commands (/start, /help)
    - User identification via chat_id
    """
    data = await request.json()
    
    chat_id = data["message"]["chat"]["id"]
    message_text = data["message"]["text"]
    user_name = data["message"]["from"]["first_name"]
    
    # Process message...
    # Generate response...
    # Send via Telegram Bot API (FREE)
```

**Why Telegram Bot API?**
- ✅ 100% FREE with no limits for personal use
- ✅ No credit card required
- ✅ Simple webhook setup
- ✅ Reliable and fast
- ✅ Better for cloud deployment (no audio processing needed)

**Alternative Option: WhatsApp via Twilio (Free Trial)**

Only use if you specifically need WhatsApp. Requires Twilio account with $15 free trial credit.

**Voice Note Handling:**
Since Web Speech API runs in the browser and Render deployment doesn't support local audio processing:
- Voice notes are NOT supported in messaging interfaces
- Users are directed to use the web dashboard for voice conversations
- Text-only messaging is supported on Telegram/WhatsApp

## Data Models

### Database Schema (Cloudflare D1 - SQLite)

> **✅ Cloudflare D1 Advantages**: 
> - **SQLite in the cloud** - persistent storage across edge locations
> - **5GB free storage** - 10x more than Supabase free tier
> - **5M reads/day, 100K writes/day** - sufficient for personal use
> - **Automatic backups** - point-in-time recovery with 30-day retention
> - **Global replication** - data available at 300+ edge locations
> - For local development, use SQLite directly

**users table:**
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    phone_number TEXT UNIQUE,
    name TEXT,
    preferred_language TEXT,
    created_at TIMESTAMP,
    last_active TIMESTAMP
);
```

**conversations table:**
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    interface TEXT,  -- 'web', 'telegram', or 'whatsapp'
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**messages table:**
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    role TEXT,  -- 'user' or 'assistant'
    content TEXT,
    language TEXT,
    message_type TEXT,  -- 'text', 'voice', 'grammar_check'
    metadata JSON,  -- Additional data (corrections, audio_url, etc.)
    timestamp TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

**grammar_corrections table:**
```sql
CREATE TABLE grammar_corrections (
    id TEXT PRIMARY KEY,
    message_id TEXT,
    original_text TEXT,
    corrected_text TEXT,
    errors JSON,  -- Array of GrammarError objects
    timestamp TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id)
);
```

### Vector Database Schema (ChromaDB)

**facts collection:**
```python
collection_config = {
    "name": "user_facts",
    "metadata": {
        "description": "Personal facts and context about users"
    },
    "embedding_function": "sentence-transformers/all-MiniLM-L6-v2"
}

# Document structure
{
    "id": "fact_uuid",
    "document": "Abhishek is my friend who works on robotics projects",
    "metadata": {
        "user_id": "user_123",
        "entity": "Abhishek",
        "relation": "friend",
        "attribute": "occupation",
        "value": "robotics projects",
        "timestamp": "2025-12-08T10:30:00Z"
    },
    "embedding": [0.123, -0.456, ...]  # Generated automatically
}
```

## Error Handling

### Error Categories

**1. External Service Failures:**
- Groq API rate limits or downtime
- Whisper API failures
- TTS service unavailability
- Twilio webhook delivery failures

**Strategy:**
- Implement exponential backoff retry logic
- Fallback to cached responses for common queries
- Queue messages for later processing if service down
- Return graceful error messages to user

**2. Audio Processing Errors:**
- Poor audio quality
- Unsupported audio formats
- Transcription confidence too low

**Strategy:**
- Validate audio format before processing
- Check transcription confidence scores
- Request user to repeat if confidence < 0.6
- Provide helpful error messages ("I couldn't hear you clearly, could you try again?")

**3. Language Detection Failures:**
- Ambiguous or mixed-language input
- Unsupported languages

**Strategy:**
- Default to English if confidence < 0.7
- Ask user to clarify language preference
- Log ambiguous cases for model improvement

**4. Database Errors:**
- Connection failures
- Write conflicts
- Storage limits

**Strategy:**
- Implement connection pooling with retry
- Use transactions for critical operations
- Monitor storage usage and alert before limits
- Graceful degradation (continue without persistence if needed)

### Error Response Format

```python
@dataclass
class ErrorResponse:
    error_code: str
    message: str  # User-friendly message
    details: Optional[str]  # Technical details (logged, not shown to user)
    retry_after: Optional[int]  # Seconds to wait before retry
    fallback_action: Optional[str]  # Suggested alternative action
```

## Testing Strategy

### Unit Testing

**Grammar Guardian Tests:**
- Test error detection for each grammar category
- Verify explanation quality and clarity
- Test edge cases (empty input, very long text, special characters)

**Polyglot Engine Tests:**
- Test language detection accuracy with sample texts
- Verify TTS service selection logic
- Test code-mixed input handling

**Knowledge Vault Tests:**
- Test fact extraction from various conversation types
- Verify embedding generation and storage
- Test context retrieval relevance

**Test Framework:** pytest with async support (pytest-asyncio)

### Integration Testing

**End-to-End Flows:**
- Complete grammar correction flow (input → LLM → response)
- Voice conversation flow (audio → STT → LLM → TTS → audio)
- WhatsApp message flow (webhook → processing → Twilio response)
- Cross-device conversation continuity

**Test Framework:** pytest with mocked external services

### Property-Based Testing

Property-based tests will be used to verify universal properties across all inputs. Each property test will run a minimum of 100 iterations with randomly generated inputs.

**Test Configuration:**
- Framework: Hypothesis (Python)
- Minimum iterations: 100 per property
- Random seed: Fixed for reproducibility during development
- Shrinking: Enabled to find minimal failing examples

**Tagging Convention:**
Each property-based test must include a comment tag in this exact format:
```python
# Feature: keliva, Property {number}: {property_text}
```

This tag explicitly links the test to its corresponding correctness property in this design document.



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Grammar error detection completeness
*For any* English text containing grammatical errors, the Grammar Guardian should identify at least one error and provide both a corrected version and an explanation with error categorization.
**Validates: Requirements 1.1, 1.2, 1.4**

### Property 2: Language mirroring consistency
*For any* user input in a supported language (English, Kannada, Telugu), the system should respond in the same language as the input, and language switches should be handled seamlessly across conversation turns.
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 3: Voice pipeline completeness
*For any* audio input during a voice call, the system should produce an audio response (transcription → processing → TTS conversion) without dropping any step in the pipeline.
**Validates: Requirements 2.3, 2.4**

### Property 4: Fact extraction and storage
*For any* user message containing personal information (names, relationships, events), the Knowledge Vault should extract at least one fact and store it with proper entity and relation metadata.
**Validates: Requirements 4.1**

### Property 5: Fact retrieval round-trip
*For any* fact stored in the Knowledge Vault, querying with the entity name should retrieve that fact in subsequent conversations, demonstrating persistence and retrieval capability.
**Validates: Requirements 4.2, 4.4, 9.3**

### Property 6: Cross-platform conversation continuity
*For any* message sent through one interface (WhatsApp or web), that message should be accessible and visible when the user switches to the other interface, maintaining complete conversation history.
**Validates: Requirements 5.5, 9.2**

### Property 7: Message persistence
*For any* conversation message (user or assistant), the system should store it in the database with a timestamp and session identifier, and it should be retrievable in future sessions.
**Validates: Requirements 9.1, 9.4, 9.5**

### Property 8: WhatsApp voice note transcription
*For any* voice note sent via WhatsApp, the system should produce a text transcription and respond with a text message (not audio) for mobile readability.
**Validates: Requirements 5.2, 5.4**

### Property 9: Real-time grammar analysis trigger
*For any* text input in the Study Room, typing should trigger a grammar analysis request to the Grammar Guardian, demonstrating real-time processing.
**Validates: Requirements 6.2**

### Property 10: Grammar error visualization
*For any* detected grammar error, the Study Room should display a visual highlight and explanation tooltip, making errors immediately visible to the user.
**Validates: Requirements 6.3**

### Property 11: Voice call transcription display
*For any* active voice call, both user speech and AI responses should produce visible transcriptions in real-time on the Study Room interface.
**Validates: Requirements 6.5**

### Property 12: AI identity concealment
*For any* response generated by the system, the text should not contain phrases that reveal AI nature (e.g., "As an AI", "I'm an artificial intelligence", "I'm a language model"), maintaining the Vani persona.
**Validates: Requirements 7.5**

### Property 13: API rate limit enforcement
*For any* sequence of requests, when the daily rate limit is approached (1,000 for 70B model, 14,000 for 8B model), the system should stop making additional requests and return an appropriate error message.
**Validates: Requirements 10.3**

### Property 14: Code-mixed transcription handling
*For any* audio input containing code-mixed language (e.g., English with Kannada/Telugu words), the STT service should produce a transcription that preserves the mixed-language content.
**Validates: Requirements 11.3**

### Property 15: Transcription formatting
*For any* completed transcription, the output text should have proper word boundaries (spaces between words) and basic punctuation, demonstrating structural correctness.
**Validates: Requirements 11.4**

### Property 16: Low-confidence transcription handling
*For any* transcription with confidence score below 0.6, the system should request clarification from the user rather than proceeding with potentially incorrect text.
**Validates: Requirements 11.5**

### Property 17: Voice consistency across sessions
*For any* two responses generated in different sessions for the same user, the TTS voice settings (voice ID, language, rate) should remain consistent, maintaining the Vani persona's voice identity.
**Validates: Requirements 12.4**

### Property 18: Audio streaming behavior
*For any* TTS audio response, the audio should be delivered in multiple chunks (not as a single complete file), demonstrating progressive streaming to reduce latency.
**Validates: Requirements 12.5**

### Property 19: Entity relationship preservation
*For any* stored fact with relationships (e.g., "Abhishek is a friend"), querying for the entity should return all associated relationships and attributes, demonstrating graph structure preservation.
**Validates: Requirements 4.4**

### Property 20: Session context continuity
*For any* user returning after a time gap (simulated by creating a new session), previously stored facts and conversation history should remain accessible, demonstrating long-term persistence.
**Validates: Requirements 4.5, 9.4**

## Deployment Architecture

### Hosting Strategy (Cloudflare - RECOMMENDED)

**Why Cloudflare over Render:**
- ✅ 10-20x faster (edge network vs single region)
- ✅ No cold starts (vs 5-15 second cold starts on Render)
- ✅ 5GB database storage (vs ephemeral storage on Render free tier)
- ✅ 100,000 requests/day free (sufficient for personal use)
- ✅ Global edge deployment (300+ cities)
- ✅ Python support via Cloudflare Pages Functions

**Service Configuration (wrangler.toml):**
```toml
name = "keliva"
compatibility_date = "2024-01-01"

[[d1_databases]]
binding = "DB"
database_name = "keliva-db"
database_id = "your-database-id"

[vars]
TELEGRAM_WEBHOOK_URL = "https://keliva.pages.dev/api/telegram/webhook"
USE_WEB_SPEECH_API = "true"
USE_EDGE_TTS = "true"
```

**Database: Cloudflare D1 (SQLite in the cloud)**
- 5GB free storage
- 5,000,000 reads/day
- 100,000 writes/day
- Automatic backups
- Global replication

**Backend Deployment:**
```bash
# Deploy FastAPI backend to Cloudflare Pages Functions
wrangler pages deploy functions --project-name=keliva
```

**Your URLs:**
- Backend: `https://keliva.pages.dev/api/*`
- Frontend: `https://keliva-app.pages.dev`

### Frontend Deployment

**Hosting:** Cloudflare Pages (free tier)
**Build Configuration:**
```bash
cd frontend
npm run build
wrangler pages deploy dist --project-name=keliva-app
```

**Environment Variables:**
```
VITE_API_URL=https://keliva.pages.dev
VITE_WS_URL=wss://keliva.pages.dev
```

**Performance Comparison:**

| Metric | Cloudflare | Render |
|--------|-----------|--------|
| Cold Start | 0ms | 5-15 seconds |
| Warm Request | 15-30ms | 200-500ms |
| Database Query | 5-10ms | 50-100ms |
| Uptime | 99.99% | 99% (sleeps) |

**See CLOUDFLARE_SETUP.md for complete deployment guide.**

## Security Considerations

### API Key Management
- All API keys stored as environment variables
- Never commit keys to version control
- Rotate keys periodically
- Use separate keys for development and production

### User Data Protection
- Encrypt sensitive user data at rest
- Use HTTPS for all communications
- Implement rate limiting to prevent abuse
- Sanitize user inputs to prevent injection attacks

### WhatsApp Security
- Validate Twilio webhook signatures
- Implement message verification
- Rate limit per phone number
- Block suspicious patterns

## Performance Optimization

### Caching Strategy
- Cache common grammar corrections
- Cache language detection results for similar inputs
- Cache TTS audio for repeated phrases
- Use Redis for distributed caching if scaling

### Database Optimization
- Index frequently queried fields (user_id, timestamp)
- Implement connection pooling
- Use prepared statements
- Regular VACUUM operations for SQLite

### Audio Processing Optimization
- Use appropriate audio formats (Opus for streaming)
- Compress audio before transmission
- Implement adaptive bitrate based on connection quality
- Buffer audio chunks for smooth playback

## Monitoring and Observability

### Metrics to Track
- API response times (p50, p95, p99)
- Error rates by endpoint
- LLM token usage and costs
- WebSocket connection duration
- Database query performance
- Audio processing latency

### Logging Strategy
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include request IDs for tracing
- Separate logs for different components
- Rotate logs to prevent disk space issues

### Alerting
- Alert on error rate > 5%
- Alert on API rate limit approaching (80% threshold)
- Alert on database storage > 80% capacity
- Alert on health check failures

## Future Enhancements

### Phase 2 Features
- Support for additional Indian languages (Hindi, Tamil, Malayalam)
- Voice cloning for more personalized Vani persona
- Emotion detection from voice tone
- Gamification elements (streaks, achievements)
- Group conversation support

### Phase 3 Features
- Mobile native apps (iOS, Android)
- Offline mode with local LLM
- Integration with learning management systems
- Teacher dashboard for monitoring student progress
- Custom vocabulary and grammar focus areas

### Scalability Considerations
- Migrate from SQLite to PostgreSQL for multi-user support
- Implement message queue (RabbitMQ/Redis) for async processing
- Use CDN for static assets and cached audio
- Implement horizontal scaling with load balancer
- Consider serverless functions for specific tasks
