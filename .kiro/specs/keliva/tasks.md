# Implementation Plan

> **💰 Cost-Free Implementation**: This project uses 100% FREE services with no credit card required!
> - **Groq API**: FREE (14,000 requests/day for 8B model, 1,000/day for 70B)
> - **Edge TTS**: FREE for all languages (English, Kannada, Telugu)
> - **Web Speech API / Vosk**: FREE for speech-to-text
> - **Total Monthly Cost**: $0 (vs $172/month with paid alternatives)
> 
> See [FREE_SERVICES_GUIDE.md](../../../FREE_SERVICES_GUIDE.md) for detailed setup instructions.

- [x] 1. Set up project structure and development environment

  - Create backend directory with FastAPI project structure (main.py, routers/, services/, models/, utils/)
  - Create frontend directory with React + Vite project structure
  - Set up Python virtual environment and install core dependencies (FastAPI, uvicorn, python-dotenv)
  - Set up Node.js project with React, TypeScript, and Vite
  - Create .env.example files for both backend and frontend with required API keys
  - Initialize Git repository with .gitignore for Python and Node.js
  - _Requirements: 8.1, 8.2_

- [x] 2. Implement database models and initialization

  - **Using Cloudflare D1 (SQLite in the cloud) - RECOMMENDED**
    - Create SQLite schema with users, conversations, messages, and grammar_corrections tables (schema.sql already created)
    - Use Cloudflare D1 bindings for database access in FastAPI
    - 5GB free storage, 5M reads/day, 100K writes/day
    - Deploy with Wrangler CLI: `wrangler d1 create keliva-db`
    - Apply schema: `wrangler d1 execute keliva-db --file=schema.sql`
    - See CLOUDFLARE_SETUP.md for complete deployment guide
  - Create Pydantic models for User, Conversation, Message, and GrammarCorrection
  - Implement database access methods using D1 bindings (request.state.env.DB)
  - Implement basic CRUD operations for each model
  - _Requirements: 9.1, 9.5, 9.6_

- [ ]* 2.1 Write property test for message persistence
  - **Property 7: Message persistence**
  - **Validates: Requirements 9.1, 9.4, 9.5**

- [x] 3. Implement Grammar Guardian service (FREE - Groq API)



  - Create GrammarGuardian class with analyze_text method
  - Integrate Groq API client with 70B model configuration (FREE - 1,000 requests/day)
  - Implement prompt engineering for grammar correction with error categorization
  - Parse LLM response to extract errors, corrections, and explanations
  - Create GrammarError and GrammarAnalysis data classes
  - Implement error highlighting position calculation
  - _Requirements: 1.1, 1.2, 1.4_

- [ ]* 3.1 Write property test for grammar error detection
  - **Property 1: Grammar error detection completeness**
  - **Validates: Requirements 1.1, 1.2, 1.4**

- [x] 4. Implement Polyglot Engine for language detection (FREE - Groq API)


  - Create PolyglotEngine class with detect_language method
  - Implement LLM-based language detection using Groq 8B model (FREE - 14,000 requests/day)
  - Add fallback character set analysis for Kannada/Telugu Unicode ranges
  - Create Language enum (ENGLISH, KANNADA, TELUGU)
  - Implement confidence threshold logic (default to English if < 0.7)
  - _Requirements: 3.1_

- [ ]* 4.1 Write property test for language detection
  - **Property 2: Language mirroring consistency (detection part)**
  - **Validates: Requirements 3.1**

- [x] 5. Implement TTS service integration (100% FREE - Edge TTS)





  - Create TTS service abstraction layer
  - Integrate Edge TTS library for English (FREE alternative to Deepgram)
  - Integrate Edge TTS library for Kannada and Telugu
  - Implement TTS service selection based on detected language
  - Create audio streaming functionality for progressive delivery
  - Store TTS configuration (voice IDs, rates) in constants
  - _Requirements: 12.1, 12.2, 12.3, 12.5_

- [ ]* 5.1 Write property test for audio streaming
  - **Property 18: Audio streaming behavior**
  - **Validates: Requirements 12.5**

- [ ]* 5.2 Write property test for voice consistency
  - **Property 17: Voice consistency across sessions**
  - **Validates: Requirements 12.4**

- [x] 6. Implement STT service integration (100% FREE - Web Speech API only)




  - Integrate Web Speech API for browser-based speech-to-text (FREE, runs in browser)
  - Implement WebSocket protocol to send transcribed text to backend
  - Add transcription confidence score checking
  - Implement low-confidence handling (request clarification if < 0.6)
  - Note: Vosk NOT used as it requires local deployment (incompatible with Render cloud)
  - Note: All speech recognition happens client-side in the browser
  - _Requirements: 11.1, 11.3, 11.4, 11.5, 11.6_

- [ ]* 6.1 Write property test for transcription formatting
  - **Property 15: Transcription formatting**
  - **Validates: Requirements 11.4**

- [ ]* 6.2 Write property test for low-confidence handling
  - **Property 16: Low-confidence transcription handling**
  - **Validates: Requirements 11.5**

- [ ]* 6.3 Write property test for code-mixed transcription
  - **Property 14: Code-mixed transcription handling**
  - **Validates: Requirements 11.3**

- [x] 7. Implement Knowledge Vault (RAG system)





  - Set up ChromaDB with sentence-transformers embedding function
  - Create KnowledgeVault class with extract_facts, store_fact, and retrieve_context methods
  - Implement fact extraction using LLM with structured output prompt
  - Create Fact and EntityGraph data classes
  - Implement semantic search for context retrieval (top-k=5)
  - Build entity relationship graph functionality
  - _Requirements: 4.1, 4.2, 4.4_

- [ ]* 7.1 Write property test for fact extraction
  - **Property 4: Fact extraction and storage**
  - **Validates: Requirements 4.1**

- [ ]* 7.2 Write property test for fact retrieval round-trip
  - **Property 5: Fact retrieval round-trip**
  - **Validates: Requirements 4.2, 4.4, 9.3**

- [ ]* 7.3 Write property test for entity relationships
  - **Property 19: Entity relationship preservation**
  - **Validates: Requirements 4.4**

- [ ]* 7.4 Write property test for session context continuity
  - **Property 20: Session context continuity**
  - **Validates: Requirements 4.5, 9.4**

- [x] 8. Implement Vani persona system




  - Create persona prompt template with personality guidelines
  - Implement context injection for retrieved facts
  - Create conversation history formatting for LLM context
  - Implement language-specific persona adjustments
  - Add emotional tone adaptation based on user sentiment
  - Implement AI identity concealment filters (remove "As an AI" phrases)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 8.1 Write property test for AI identity concealment
  - **Property 12: AI identity concealment**
  - **Validates: Requirements 7.5**


- [x] 9. Implement core conversation flow



  - Create conversation service that orchestrates all components
  - Implement text message processing pipeline (input → language detection → LLM → response)
  - Integrate Knowledge Vault context retrieval into conversation flow
  - Implement language mirroring logic (respond in same language as input)
  - Add conversation history management
  - Store all messages in database with proper metadata
  - _Requirements: 3.2, 3.3, 3.4, 3.5, 4.3_

- [ ]* 9.1 Write property test for language mirroring
  - **Property 2: Language mirroring consistency**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [x] 10. Implement REST API endpoints


  - Create FastAPI router for grammar checking (POST /api/grammar/check)
  - Create router for text chat (POST /api/chat/message)
  - Create router for conversation history (GET /api/conversation/history)
  - Create health check endpoint (GET /api/health)
  - Implement request validation with Pydantic models
  - Add error handling and appropriate HTTP status codes
  - _Requirements: 1.1, 8.3_

- [x] 11. Implement WebSocket for voice calls



  - Create WebSocket endpoint (WS /api/voice/stream)
  - Implement bidirectional audio streaming protocol
  - Handle audio chunk reception and buffering
  - Integrate STT for real-time transcription
  - Integrate TTS for audio response generation
  - Implement streaming response delivery
  - Add connection management (connect, disconnect, error handling)
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 11.1 Write property test for voice pipeline
  - **Property 3: Voice pipeline completeness**
  - **Validates: Requirements 2.3, 2.4**

- [x] 12. Implement API rate limiting


  - Create rate limiter service to track API usage
  - Implement counters for Groq 70B (1,000/day) and 8B (14,000/day) models
  - Add middleware to check rate limits before API calls
  - Return appropriate error messages when limits exceeded
  - Implement daily reset logic
  - Store rate limit data in database or Redis
  - _Requirements: 10.3_

- [ ]* 12.1 Write property test for rate limit enforcement
  - **Property 13: API rate limit enforcement**
  - **Validates: Requirements 10.3**

- [x] 13. Implement Telegram Bot integration (100% FREE - Recommended)




  - Set up Telegram Bot API with bot token (get from @BotFather)
  - Create webhook endpoint (POST /api/telegram/webhook)
  - Implement webhook signature validation for security
  - Parse incoming text messages from webhook payload
  - Create message sending functionality via Telegram Bot API (FREE)
  - Implement command handlers (/start, /help)
  - Add error handling for API failures
  - Note: Voice notes NOT supported (direct users to web interface for voice)
  - _Requirements: 5.1, 5.3, 5.4, 5.5, 5.6_

- [ ]* 13.1 (Optional) Implement WhatsApp integration with Twilio
  - Only implement if Telegram is not sufficient
  - Set up Twilio client with account credentials (uses free trial credit)
  - Create webhook endpoint (POST /api/whatsapp/webhook)
  - Parse incoming text messages only (no voice note support)
  - _Requirements: 5.1, 5.3, 5.4, 5.5_

- [ ]* 13.2 Write property test for message delivery
  - **Property 8: Messaging platform message delivery**
  - **Validates: Requirements 5.1, 5.3**

- [x] 14. Implement cross-platform conversation continuity



  - Ensure all messages (WhatsApp and web) use same conversation storage
  - Implement session management across interfaces
  - Add user identification logic (phone number for WhatsApp, session ID for web)
  - Create conversation retrieval that includes messages from all interfaces
  - Test message visibility across platforms
  - _Requirements: 5.5, 9.2_

- [ ]* 14.1 Write property test for cross-platform continuity
  - **Property 6: Cross-platform conversation continuity**
  - **Validates: Requirements 5.5, 9.2**

- [x] 15. Checkpoint - Ensure all backend tests pass




  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Build React frontend - Study Room layout





  - Create main Dashboard component with layout
  - Implement navigation and routing (React Router)
  - Create GrammarEditor component with text input area
  - Create VoiceCall component with call controls
  - Create ChatHistory component for message display
  - Implement responsive design with CSS/Tailwind
  - _Requirements: 6.1_

- [x] 17. Implement real-time grammar checking UI




  - Create text input with onChange handler
  - Implement API call to grammar check endpoint
  - Create ErrorHighlight component for visual indicators
  - Create ExplanationTooltip component for error details
  - Implement error position mapping and highlighting
  - Add loading states and error handling
  - _Requirements: 6.2, 6.3_

- [ ]* 17.1 Write property test for grammar analysis trigger
  - **Property 9: Real-time grammar analysis trigger**
  - **Validates: Requirements 6.2**

- [ ]* 17.2 Write property test for error visualization
  - **Property 10: Grammar error visualization**
  - **Validates: Requirements 6.3**

- [x] 18. Implement WebSocket voice call UI





  - Create WebSocket connection hook (useWebSocket)
  - Implement microphone access and audio capture
  - Create audio visualizer component (waveform display)
  - Implement audio chunk sending over WebSocket
  - Create audio playback for received responses
  - Display real-time transcription of user and AI speech
  - Add call controls (start, stop, mute)
  - _Requirements: 2.1, 6.4, 6.5_

- [ ]* 18.1 Write property test for transcription display
  - **Property 11: Voice call transcription display**
  - **Validates: Requirements 6.5**

- [x] 19. Implement conversation history display

  - Create message list component with scrolling
  - Implement message fetching from API
  - Display messages with timestamps and sender info
  - Add message formatting (user vs assistant styling)
  - Implement auto-scroll to latest message
  - Add loading states and pagination
  - _Requirements: 9.1, 9.2_

- [x] 20. Implement frontend state management



  - Set up React Context for global state (user, conversation)
  - Create authentication context (if needed)
  - Implement conversation state management
  - Create custom hooks for API calls
  - Add error boundary components
  - _Requirements: 6.1_

- [x] 21. Add frontend error handling and loading states

  - Implement error toast notifications
  - Create loading spinners for async operations
  - Add retry logic for failed API calls
  - Implement offline detection and messaging
  - Create fallback UI for component errors
  - _Requirements: 6.1_

- [x] 22. Implement deployment configuration (Cloudflare)


  - Create wrangler.toml configuration (already created)
  - Create D1 database: `wrangler d1 create keliva-db`
  - Apply database schema: `wrangler d1 execute keliva-db --file=schema.sql`
  - Set secrets: `wrangler secret put GROQ_API_KEY` and `wrangler secret put TELEGRAM_BOT_TOKEN`
  - Deploy backend: `wrangler pages deploy functions --project-name=keliva`
  - Deploy frontend: `wrangler pages deploy frontend/dist --project-name=keliva-app`
  - Set Telegram webhook to Cloudflare URL
  - See CLOUDFLARE_SETUP.md for complete step-by-step guide
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 23. Add security measures
  - Implement CORS configuration for frontend origin
  - Add request validation and sanitization
  - Implement Twilio webhook signature verification
  - Add rate limiting per IP address
  - Implement API key rotation mechanism
  - Add input sanitization to prevent injection attacks
  - _Requirements: 5.1_

- [ ] 24. Implement logging and monitoring
  - Set up structured logging with Python logging module
  - Add request ID tracking for tracing
  - Implement error logging with stack traces
  - Create performance metrics logging (response times)
  - Add API usage tracking for cost monitoring
  - Set up log rotation to prevent disk space issues
  - _Requirements: 10.3_

- [ ]* 24.1 Write integration tests for logging
  - Test that errors are properly logged
  - Test that request IDs are tracked
  - _Requirements: 10.3_

- [ ] 25. Create documentation
  - Write README.md with project overview and setup instructions
  - Document API endpoints with request/response examples
  - Create environment variable documentation
  - Write deployment guide for Render and Vercel
  - Document Twilio webhook setup process
  - Create user guide for Study Room features
  - _Requirements: All_

- [ ] 26. Final checkpoint - End-to-end testing
  - Ensure all tests pass, ask the user if questions arise.
