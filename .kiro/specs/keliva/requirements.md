# Requirements Document

> **💰 Cost-Free Solution**: All requirements are designed to be implemented using 100% FREE services!
> - No credit card required for core functionality
> - Groq API (FREE), Edge TTS (FREE), Web Speech API/Vosk (FREE)
> - Total monthly cost: $0

## Introduction

KeLiva (Knowledge-Enhanced Linguistic Intelligence & Voice Assistant) is an AI-powered companion application that serves as both a strict English tutor and a supportive friend. The system provides personalized language learning and emotional support through natural conversations in multiple languages (English, Kannada, Telugu). It operates across two interfaces: a web dashboard for focused study sessions and WhatsApp integration for casual, on-the-go interactions. The AI maintains contextual memory of user conversations, personal details, and relationships to provide deeply personalized responses.

## Glossary

- **KeLiva System**: The complete AI companion application including backend server, web dashboard, and WhatsApp integration
- **Central Brain**: The FastAPI backend server hosted on Render that processes all requests and maintains conversation state
- **Grammar Guardian**: The intelligent grammar correction engine that identifies and explains English language mistakes
- **Polyglot Engine**: The language detection and switching system that handles English, Kannada, and Telugu
- **Knowledge Vault**: The RAG-based long-term memory system that stores and retrieves personal context about the user
- **Study Room**: The web dashboard interface for focused learning sessions
- **Companion Interface**: The messaging integration (Telegram Bot API or WhatsApp via Twilio) for casual conversations
- **Vani**: The AI persona name with defined personality traits
- **LLM**: Large Language Model (Groq Llama 3) used for natural language understanding and generation
- **STT**: Speech-to-Text conversion service (Web Speech API or Vosk - both FREE)
- **TTS**: Text-to-Speech conversion service (Edge TTS - FREE)
- **RAG**: Retrieval-Augmented Generation for context-aware responses
- **WebSocket**: Real-time bidirectional communication protocol for voice calls

## Requirements

### Requirement 1

**User Story:** As an English learner, I want real-time grammar correction with explanations, so that I can understand and learn from my mistakes immediately.

#### Acceptance Criteria

1. WHEN a user types text in English THEN the Grammar Guardian SHALL identify grammatical errors and highlight them
2. WHEN a grammatical error is identified THEN the Grammar Guardian SHALL provide the corrected version with a clear explanation of the mistake type
3. WHEN the user submits text for correction THEN the KeLiva System SHALL use the Groq 70B model to ensure high-quality grammar analysis
4. WHEN displaying corrections THEN the Grammar Guardian SHALL categorize errors by type (tense, article, preposition, etc.)
5. WHEN a correction is provided THEN the Grammar Guardian SHALL present it in a friendly, encouraging tone consistent with the Vani persona

### Requirement 2

**User Story:** As a user, I want to have voice conversations with the AI in real-time, so that I can practice speaking English naturally without delays.

#### Acceptance Criteria

1. WHEN a user initiates a voice call through the Study Room THEN the KeLiva System SHALL establish a WebSocket connection for bidirectional audio streaming
2. WHEN the user speaks during a voice call THEN the STT service SHALL transcribe the audio to text with minimal latency
3. WHEN audio transcription is complete THEN the Central Brain SHALL process the text and generate a response using streaming
4. WHEN the LLM generates a response THEN the TTS service SHALL convert text to speech and stream audio back to the user immediately
5. WHEN streaming audio responses THEN the KeLiva System SHALL maintain end-to-end latency under 2 seconds to simulate natural conversation

### Requirement 3

**User Story:** As a multilingual user, I want to speak in my native language (Kannada or Telugu) for emotional support, so that I can express myself naturally when I'm stressed or need comfort.

#### Acceptance Criteria

1. WHEN a user speaks in any supported language THEN the Polyglot Engine SHALL automatically detect the language (English, Kannada, or Telugu)
2. WHEN the detected language is Kannada THEN the KeLiva System SHALL respond in Kannada using appropriate TTS voices
3. WHEN the detected language is Telugu THEN the KeLiva System SHALL respond in Telugu using appropriate TTS voices
4. WHEN the detected language is English THEN the KeLiva System SHALL respond in English and activate tutor mode for grammar correction
5. WHEN the user switches languages mid-conversation THEN the Polyglot Engine SHALL adapt the response language accordingly without requiring manual configuration

### Requirement 4

**User Story:** As a user seeking companionship, I want the AI to remember personal details about my life, friends, and family, so that conversations feel natural and personalized.

#### Acceptance Criteria

1. WHEN a user mentions a personal fact (name, relationship, event) THEN the Knowledge Vault SHALL extract and store the entity, relation, and context
2. WHEN a user refers to a previously mentioned person or event THEN the Central Brain SHALL retrieve relevant context from the Knowledge Vault before generating a response
3. WHEN generating responses THEN the KeLiva System SHALL incorporate retrieved personal context to make replies contextually aware
4. WHEN storing facts THEN the Knowledge Vault SHALL maintain relationships between entities (e.g., "Abhishek is a friend who works on robotics projects")
5. WHEN the user mentions the same entity across different sessions THEN the KeLiva System SHALL maintain continuity of context over time

### Requirement 5

**User Story:** As a mobile user, I want to chat with the AI through messaging apps (Telegram or WhatsApp) using text and voice notes, so that I can practice English conveniently throughout my day.

#### Acceptance Criteria

1. WHEN a user sends a text message via Telegram THEN the Companion Interface SHALL receive the message through Telegram Bot API and forward it to the Central Brain at zero cost
2. WHEN a user sends a voice note via messaging app THEN the Companion Interface SHALL transcribe the audio using Web Speech API and process it as text input
3. WHEN the Central Brain generates a response THEN the Companion Interface SHALL send the reply through the appropriate API (Telegram Bot API or Twilio API)
4. WHEN responding to voice notes THEN the KeLiva System SHALL provide text responses by default for mobile readability
5. WHEN a messaging conversation occurs THEN the KeLiva System SHALL maintain conversation history consistent with web dashboard sessions
6. WHEN using Telegram Bot API THEN the system SHALL operate at zero cost with no rate limits for personal use

### Requirement 6

**User Story:** As a desktop user, I want a web dashboard with live grammar checking and voice call features, so that I can have focused study sessions with immediate feedback.

#### Acceptance Criteria

1. WHEN a user accesses the Study Room THEN the web dashboard SHALL display an interface with text input, grammar feedback panel, and voice call controls
2. WHEN a user types in the text input field THEN the Study Room SHALL send text to the Grammar Guardian for real-time analysis
3. WHEN grammar errors are detected THEN the Study Room SHALL highlight mistakes with visual indicators and display explanation tooltips
4. WHEN a user clicks the voice call button THEN the Study Room SHALL initiate a WebSocket connection and enable microphone access
5. WHEN a voice call is active THEN the Study Room SHALL display real-time transcription of both user speech and AI responses

### Requirement 7

**User Story:** As a user, I want the AI to have a consistent, empathetic personality that understands Indian cultural context, so that interactions feel natural and supportive.

#### Acceptance Criteria

1. WHEN generating any response THEN the Vani persona SHALL use empathetic, encouraging language appropriate to the user's emotional state
2. WHEN the user expresses sadness or stress THEN the Vani persona SHALL respond with soft, comforting language
3. WHEN the user expresses happiness or excitement THEN the Vani persona SHALL respond with enthusiastic, celebratory language
4. WHEN appropriate to context THEN the Vani persona SHALL reference Indian cultural elements (festivals, food, family dynamics)
5. WHEN responding THEN the Vani persona SHALL never identify as an AI but maintain the illusion of being a real friend

### Requirement 8

**User Story:** As a user, I want the system to be available 24/7 without downtime, so that I can access my AI companion whenever I need support or practice.

#### Acceptance Criteria

1. WHEN the Central Brain is deployed on Render free tier THEN the KeLiva System SHALL implement a keep-alive mechanism to prevent server sleep
2. WHEN the keep-alive mechanism is active THEN an external monitoring service SHALL ping the health check endpoint every 14 minutes
3. WHEN a health check ping is received THEN the Central Brain SHALL respond with a status confirmation to maintain active state
4. WHEN a user sends a WhatsApp message at any time THEN the Companion Interface SHALL respond within 5 seconds
5. WHEN server uptime is monitored THEN the KeLiva System SHALL maintain 99% availability over a 30-day period

### Requirement 9

**User Story:** As a user, I want my conversation history and personal context to persist across sessions and devices, so that I have continuity in my relationship with the AI.

#### Acceptance Criteria

1. WHEN a conversation occurs on any interface THEN the Central Brain SHALL store the complete message history in the database with persistent storage
2. WHEN a user switches from Telegram to web dashboard THEN the KeLiva System SHALL maintain conversation continuity with access to previous context
3. WHEN personal facts are extracted THEN the Knowledge Vault SHALL persist entity relationships in the database for future retrieval
4. WHEN a user returns after days or weeks THEN the KeLiva System SHALL recall relevant past conversations and personal details
5. WHEN storing conversation data THEN the Central Brain SHALL associate messages with timestamps and session identifiers for proper sequencing
6. WHEN deployed on Cloudflare THEN the system SHALL use Cloudflare D1 (SQLite in the cloud) with 5GB free storage for data persistence across edge locations

### Requirement 10

**User Story:** As a developer, I want the system to use different LLM models optimally, so that I can balance quality, speed, and API rate limits effectively.

#### Acceptance Criteria

1. WHEN processing grammar correction requests THEN the Central Brain SHALL use the Groq 70B model for high-quality analysis
2. WHEN processing voice conversation requests THEN the Central Brain SHALL use the Groq 8B model for faster response times
3. WHEN API rate limits are approached THEN the Central Brain SHALL track usage and prevent exceeding daily limits (1,000 for 70B, 14,000 for 8B)
4. WHEN selecting a model THEN the Central Brain SHALL route requests based on the interaction type (grammar vs. conversation)
5. WHEN model selection occurs THEN the KeLiva System SHALL maintain response quality appropriate to each use case

### Requirement 11

**User Story:** As a user, I want accurate speech recognition for Indian accents and code-mixed speech, so that the AI understands me correctly when I speak naturally.

#### Acceptance Criteria

1. WHEN processing audio input THEN the STT service SHALL use Web Speech API (browser-based, FREE) for robust multi-language and accent support at zero cost
2. WHEN a user speaks with an Indian accent THEN the STT service SHALL accurately transcribe English words without significant errors
3. WHEN a user code-mixes languages (e.g., "I am feeling tensed about my exam") THEN the STT service SHALL transcribe the mixed-language input correctly
4. WHEN transcription is complete THEN the Central Brain SHALL receive text with proper word boundaries and punctuation
5. WHEN audio quality is poor THEN the STT service SHALL attempt best-effort transcription and the system SHALL request clarification if confidence is low
6. WHEN deployed on cloud platforms (Render) THEN the system SHALL use Web Speech API exclusively as it runs in the browser without server-side processing

### Requirement 12

**User Story:** As a user, I want natural-sounding voice output in all supported languages, so that listening to the AI feels pleasant and engaging.

#### Acceptance Criteria

1. WHEN generating English speech THEN the TTS service SHALL use Edge TTS with a clear, natural accent at zero cost
2. WHEN generating Kannada speech THEN the TTS service SHALL use Edge TTS with an appropriate Indian voice
3. WHEN generating Telugu speech THEN the TTS service SHALL use Edge TTS with an appropriate Indian voice
4. WHEN producing audio output THEN the TTS service SHALL maintain consistent voice characteristics for the Vani persona across sessions
5. WHEN streaming audio THEN the TTS service SHALL deliver audio chunks progressively to minimize perceived latency
