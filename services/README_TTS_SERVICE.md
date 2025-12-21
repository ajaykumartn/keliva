# TTS Service Documentation

## Overview

The TTS (Text-to-Speech) Service provides audio generation capabilities for KeLiva using Edge TTS, a 100% FREE text-to-speech solution. It supports multiple languages (English, Kannada, Telugu) with natural-sounding voices and streaming audio delivery.

## Features

- **Multi-language Support**: English, Kannada, and Telugu
- **Audio Streaming**: Progressive delivery of audio chunks for low latency
- **Natural Voices**: High-quality neural voices from Microsoft Edge
- **Zero Cost**: Completely free with no API limits
- **Configurable Settings**: Adjustable rate, volume, and pitch

## Architecture

```
┌─────────────────────────────────────────┐
│         TTS Service                      │
│  ┌────────────────────────────────────┐ │
│  │   TTSConfig (Constants)            │ │
│  │   - Voice IDs per language         │ │
│  │   - Rate, Volume, Pitch settings   │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │   TTSService (Main Class)          │ │
│  │   - text_to_speech() - streaming   │ │
│  │   - text_to_speech_bytes() - full  │ │
│  │   - save_to_file() - file output   │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
              ▼
    ┌──────────────────┐
    │   Edge TTS       │
    │   (FREE)         │
    └──────────────────┘
```

## Usage Examples

### Basic Text-to-Speech (Streaming)

```python
from services.tts_service import TTSService
from services.polyglot_engine import Language

# Initialize service
tts = TTSService()

# Generate speech with streaming
async for chunk in tts.text_to_speech(
    text="Hello, how are you today?",
    language=Language.ENGLISH,
    stream=True
):
    if not chunk.is_final:
        # Send audio chunk to client
        await websocket.send_bytes(chunk.data)
    else:
        # Streaming complete
        print(f"Sent {chunk.sequence} audio chunks")
```

### Complete Audio Generation

```python
# Generate complete audio file
audio_bytes = await tts.text_to_speech_bytes(
    text="ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?",
    language=Language.KANNADA
)

# Use audio_bytes as needed (save, stream, etc.)
```

### Save to File

```python
# Save audio directly to file
await tts.save_to_file(
    text="నమస్కారం, మీరు ఎలా ఉన్నారు?",
    language=Language.TELUGU,
    output_path="output.mp3"
)
```

### Customize Voice Settings

```python
# Adjust speech parameters
tts.set_voice_settings(
    rate="+10%",    # Speak 10% faster
    volume="+5%",   # Slightly louder
    pitch="+2Hz"    # Slightly higher pitch
)

# Generate with custom settings
audio_bytes = await tts.text_to_speech_bytes(
    text="This will be spoken faster and louder",
    language=Language.ENGLISH
)
```

### Get Voice Information

```python
# Get the voice ID for a language
voice_id = tts.get_voice_for_language(Language.KANNADA)
print(f"Kannada voice: {voice_id}")  # Output: kn-IN-GaganNeural
```

## Voice Configuration

### Supported Voices

| Language | Voice ID | Gender | Description |
|----------|----------|--------|-------------|
| English | en-US-AriaNeural | Female | Clear, natural American English |
| Kannada | kn-IN-GaganNeural | Male | Natural Kannada with Indian accent |
| Telugu | te-IN-ShrutiNeural | Female | Natural Telugu with Indian accent |

### Voice Settings

- **Rate**: Speech speed adjustment
  - Format: `"+X%"` or `"-X%"` (range: -50% to +100%)
  - Default: `"+0%"` (normal speed)
  - Example: `"+20%"` = 20% faster, `"-10%"` = 10% slower

- **Volume**: Audio volume adjustment
  - Format: `"+X%"` or `"-X%"` (range: -50% to +100%)
  - Default: `"+0%"` (normal volume)
  - Example: `"+15%"` = 15% louder

- **Pitch**: Voice pitch adjustment
  - Format: `"+XHz"` or `"-XHz"` (range: -50Hz to +50Hz)
  - Default: `"+0Hz"` (normal pitch)
  - Example: `"+5Hz"` = slightly higher pitch

## Integration with Polyglot Engine

The TTS service is designed to work seamlessly with the Polyglot Engine for language detection:

```python
from services.polyglot_engine import PolyglotEngine, Language
from services.tts_service import TTSService

# Initialize services
polyglot = PolyglotEngine()
tts = TTSService()

# Detect language and generate speech
user_input = "ನಮಸ್ಕಾರ"
detected_language = await polyglot.detect_language(user_input)

# Generate response in detected language
response_text = "ನಮಸ್ಕಾರ! ನೀವು ಹೇಗಿದ್ದೀರಿ?"
async for chunk in tts.text_to_speech(response_text, detected_language):
    # Stream audio to user
    await send_audio_chunk(chunk)
```

## WebSocket Integration

For real-time voice conversations:

```python
from fastapi import WebSocket

@app.websocket("/api/voice/stream")
async def voice_stream(websocket: WebSocket):
    await websocket.accept()
    
    tts = TTSService()
    
    try:
        while True:
            # Receive text from client
            data = await websocket.receive_json()
            text = data["text"]
            language = Language(data["language"])
            
            # Stream audio response
            async for chunk in tts.text_to_speech(text, language):
                if not chunk.is_final:
                    await websocket.send_json({
                        "type": "audio_chunk",
                        "data": chunk.data.hex(),  # Convert bytes to hex string
                        "sequence": chunk.sequence
                    })
                else:
                    await websocket.send_json({
                        "type": "audio_complete",
                        "total_chunks": chunk.sequence
                    })
    except Exception as e:
        await websocket.close()
```

## Error Handling

```python
from services.tts_service import TTSService
from services.polyglot_engine import Language

tts = TTSService()

try:
    audio = await tts.text_to_speech_bytes(
        text="Hello world",
        language=Language.ENGLISH
    )
except ValueError as e:
    # Unsupported language
    print(f"Language error: {e}")
except Exception as e:
    # TTS generation failed
    print(f"TTS error: {e}")
```

## Performance Considerations

### Streaming vs. Complete Audio

- **Streaming** (`text_to_speech`):
  - Lower latency - audio starts playing immediately
  - Better for real-time conversations
  - Recommended for voice calls

- **Complete** (`text_to_speech_bytes`):
  - Higher latency - waits for complete generation
  - Better for caching or file storage
  - Recommended for pre-generated responses

### Caching Strategy

For frequently used phrases:

```python
from functools import lru_cache

class CachedTTSService(TTSService):
    def __init__(self):
        super().__init__()
        self.cache = {}
    
    async def get_cached_audio(self, text: str, language: Language) -> bytes:
        cache_key = f"{language.value}:{text}"
        
        if cache_key not in self.cache:
            self.cache[cache_key] = await self.text_to_speech_bytes(text, language)
        
        return self.cache[cache_key]
```

## Testing

### Unit Tests

```python
import pytest
from services.tts_service import TTSService
from services.polyglot_engine import Language

@pytest.mark.asyncio
async def test_english_tts():
    tts = TTSService()
    audio = await tts.text_to_speech_bytes("Hello", Language.ENGLISH)
    assert len(audio) > 0
    assert isinstance(audio, bytes)

@pytest.mark.asyncio
async def test_streaming_tts():
    tts = TTSService()
    chunks = []
    
    async for chunk in tts.text_to_speech("Test", Language.ENGLISH):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    assert chunks[-1].is_final

@pytest.mark.asyncio
async def test_unsupported_language():
    tts = TTSService()
    
    with pytest.raises(ValueError):
        await tts.text_to_speech_bytes("Test", Language.UNKNOWN)
```

## Requirements

- Python 3.11+
- edge-tts==6.1.9 (FREE)
- aiofiles (for file operations)

## Cost Analysis

| Service | Cost | Limits |
|---------|------|--------|
| Edge TTS | **$0/month** | No limits |
| Alternative (Deepgram) | $12/month | 45 hours |
| Alternative (Google TTS) | $16/month | 4M characters |

**Total Savings: $12-16/month per language = $36-48/month for 3 languages**

## Troubleshooting

### Common Issues

1. **No audio output**
   - Check if edge-tts is installed: `pip install edge-tts`
   - Verify language is supported
   - Check network connectivity

2. **Poor audio quality**
   - Adjust rate/volume/pitch settings
   - Ensure text is properly formatted
   - Try different voice IDs

3. **Slow generation**
   - Use streaming for better perceived performance
   - Implement caching for repeated phrases
   - Check network latency

## Future Enhancements

- Voice cloning for personalized Vani persona
- Emotion-based voice modulation
- SSML support for advanced control
- Multiple voice options per language
- Audio format selection (MP3, WAV, OGG)
