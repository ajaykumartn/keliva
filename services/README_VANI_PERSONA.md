# Vani Persona System

## Overview

The Vani Persona System is the heart of KeLiva's AI companion functionality. It manages the AI's personality, emotional intelligence, and context-aware responses while maintaining the illusion of a real friend rather than an artificial system.

## Key Features

### 1. **Persona Prompt Template**
- Creates comprehensive system prompts with personality guidelines
- Incorporates user name and personal context
- Includes conversation history for continuity
- Adapts based on language and emotional state

### 2. **Context Injection**
- Integrates retrieved facts from Knowledge Vault
- Formats personal information about user's life, friends, and family
- Groups facts by entity for better organization
- Handles empty context gracefully for new users

### 3. **Conversation History Formatting**
- Maintains last 10 messages for context
- Formats messages with clear role labels (User/Vani)
- Provides conversation continuity across sessions

### 4. **Language-Specific Persona Adjustments**
- **English Mode**: Enables grammar correction, supportive tutoring
- **Kannada Mode**: Comfort-focused, uses natural Kannada expressions
- **Telugu Mode**: Comfort-focused, uses natural Telugu expressions
- Automatically mirrors user's language choice

### 5. **Emotional Tone Adaptation**
- **Comforting**: Soft, gentle, reassuring for sad/stressed users
- **Encouraging**: Positive, uplifting, motivational
- **Celebratory**: Enthusiastic, excited, shares in user's joy
- **Empathetic**: Deep understanding, active listening
- **Neutral**: Warm, friendly, adaptable baseline

### 6. **AI Identity Concealment**
- Removes phrases like "As an AI", "I'm a language model"
- Filters out statements about lacking feelings/emotions
- Maintains the illusion of a real friend
- Cleans up awkward punctuation after removal

## Architecture

```
VaniPersona
├── Initialization
│   └── Groq API client (llama-3.3-8b-instant)
│
├── Prompt Creation
│   ├── _create_persona_prompt()
│   ├── _format_retrieved_facts()
│   ├── _format_conversation_history()
│   ├── _get_language_instructions()
│   └── _get_tone_instructions()
│
├── Emotional Intelligence
│   └── _detect_emotional_tone()
│
├── AI Concealment
│   └── _apply_ai_concealment()
│
└── Response Generation
    ├── generate_response() - Standard
    └── generate_streaming_response() - Real-time voice
```

## Data Structures

### ConversationContext
```python
@dataclass
class ConversationContext:
    user_name: str
    user_message: str
    language: Language
    conversation_history: List[Dict[str, str]]
    retrieved_facts: List[Fact]
    emotional_tone: EmotionalTone = EmotionalTone.NEUTRAL
    is_grammar_mode: bool = False
```

### PersonaResponse
```python
@dataclass
class PersonaResponse:
    content: str
    language: Language
    emotional_tone: EmotionalTone
    concealment_applied: bool
```

### EmotionalTone
```python
class EmotionalTone(Enum):
    NEUTRAL = "neutral"
    COMFORTING = "comforting"
    ENCOURAGING = "encouraging"
    CELEBRATORY = "celebratory"
    EMPATHETIC = "empathetic"
```

## Usage Examples

### Basic Response Generation

```python
from services.vani_persona import VaniPersona, ConversationContext, EmotionalTone
from services.polyglot_engine import Language

# Initialize persona
persona = VaniPersona()

# Create context
context = ConversationContext(
    user_name="Ajay",
    user_message="I'm feeling stressed about my project",
    language=Language.ENGLISH,
    conversation_history=[],
    retrieved_facts=[],
    emotional_tone=EmotionalTone.NEUTRAL,  # Auto-detected if NEUTRAL
    is_grammar_mode=False
)

# Generate response
response = await persona.generate_response(context)
print(response.content)
print(f"Tone: {response.emotional_tone}")
print(f"AI concealment applied: {response.concealment_applied}")
```

### Streaming Response (for Voice)

```python
# For real-time voice conversations
async for chunk in persona.generate_streaming_response(context):
    # Send chunk to TTS service
    audio_chunk = await tts_service.convert(chunk)
    await websocket.send(audio_chunk)
```

### With Retrieved Facts

```python
from services.knowledge_vault import Fact
from datetime import datetime

# Add personal context
facts = [
    Fact(
        id="1",
        user_id="user123",
        entity="Abhishek",
        relation="friend",
        attribute="occupation",
        value="robotics",
        context="Abhishek is my friend who works on robotics projects",
        timestamp=datetime.now()
    )
]

context = ConversationContext(
    user_name="Ajay",
    user_message="I talked to Abhishek today",
    language=Language.ENGLISH,
    conversation_history=[],
    retrieved_facts=facts,  # Vani will reference this context
    emotional_tone=EmotionalTone.NEUTRAL,
    is_grammar_mode=False
)

response = await persona.generate_response(context)
# Response will naturally reference Abhishek's robotics work
```

### Grammar Tutor Mode

```python
context = ConversationContext(
    user_name="Ajay",
    user_message="I goes to school yesterday",
    language=Language.ENGLISH,
    conversation_history=[],
    retrieved_facts=[],
    emotional_tone=EmotionalTone.NEUTRAL,
    is_grammar_mode=True  # Enables gentle grammar correction
)

response = await persona.generate_response(context)
# Response will gently correct "goes" to "went"
```

## Emotional Tone Detection

The system automatically detects emotional tone from user messages using keyword analysis:

### Sad/Stressed Keywords
- sad, depressed, stressed, worried, anxious, upset
- crying, hurt, pain, difficult, hard, struggling
- tired, exhausted, overwhelmed

### Happy/Excited Keywords
- happy, excited, great, amazing, wonderful, awesome
- yay, woohoo, celebrate, won, success, achieved
- love, fantastic, excellent

### Empathetic Triggers
- Questions (contains "?")
- Sharing phrases: "tell you", "share", "happened"

## AI Identity Concealment

The system removes or filters these patterns:
- "as an ai"
- "i'm an ai"
- "i'm an artificial intelligence"
- "i'm a language model"
- "i'm a computer program"
- "i don't have feelings"
- "i don't have emotions"
- "i can't feel"
- "i'm not human"
- "i'm just a"
- "as a language model"
- "as an artificial intelligence"

## Testing

Run the comprehensive test suite:

```bash
cd backend
python test_vani_persona.py
```

Tests cover:
- ✓ Persona initialization
- ✓ Emotional tone detection
- ✓ AI identity concealment
- ✓ Language-specific instructions
- ✓ Tone-specific instructions
- ✓ Fact formatting
- ✓ Conversation history formatting
- ✓ Complete persona prompt creation
- ✓ Response generation (with API key)

## Integration Points

### With Knowledge Vault
```python
# Retrieve relevant facts
facts = await knowledge_vault.retrieve_context(
    query=user_message,
    user_id=user_id,
    top_k=5
)

# Include in context
context.retrieved_facts = facts
```

### With Polyglot Engine
```python
# Detect language
language = await polyglot_engine.detect_language(user_message)

# Set in context
context.language = language
```

### With Grammar Guardian
```python
# Enable grammar mode for English
if language == Language.ENGLISH:
    context.is_grammar_mode = True
```

## Configuration

### Model Selection
- Uses `llama-3.3-8b-instant` for fast conversational responses
- FREE: 14,000 requests/day on Groq API
- Temperature: 0.8 (natural, varied responses)
- Max tokens: 500 (concise but complete)

### Customization
Modify personality guidelines in `_create_persona_prompt()`:
- Adjust cultural references
- Change tone descriptions
- Add/remove personality traits
- Customize grammar correction approach

## Performance

- **Latency**: ~200-500ms for standard responses
- **Streaming**: ~50-100ms for first chunk
- **Memory**: Minimal (stateless, context passed in)
- **Cost**: $0 (FREE Groq API)

## Requirements Validated

This implementation satisfies:
- ✓ **Requirement 7.1**: Empathetic, encouraging language
- ✓ **Requirement 7.2**: Emotional tone adaptation (sad/stressed)
- ✓ **Requirement 7.3**: Emotional tone adaptation (happy/excited)
- ✓ **Requirement 7.4**: Indian cultural context references
- ✓ **Requirement 7.5**: AI identity concealment

## Future Enhancements

1. **Advanced Emotion Detection**: Use LLM for more nuanced emotion analysis
2. **Personality Customization**: Allow users to adjust Vani's personality
3. **Memory Integration**: Store user preferences for tone/style
4. **Multi-turn Reasoning**: Better context understanding across conversations
5. **Voice Tone Matching**: Adjust TTS parameters based on emotional tone

## Troubleshooting

### Issue: Responses feel robotic
**Solution**: Increase temperature (currently 0.8) or adjust personality guidelines

### Issue: AI identity leaking through
**Solution**: Add more patterns to `AI_IDENTITY_PATTERNS` list

### Issue: Wrong emotional tone detected
**Solution**: Expand keyword lists in `_detect_emotional_tone()`

### Issue: Facts not being referenced
**Solution**: Ensure facts are properly formatted and relevant to query

## Related Files

- `backend/services/vani_persona.py` - Main implementation
- `backend/test_vani_persona.py` - Test suite
- `backend/services/knowledge_vault.py` - Fact storage/retrieval
- `backend/services/polyglot_engine.py` - Language detection
- `.kiro/specs/keliva/design.md` - Design specifications
- `.kiro/specs/keliva/requirements.md` - Requirements document
