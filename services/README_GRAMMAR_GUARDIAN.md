# Grammar Guardian Service

## Overview

The Grammar Guardian is an intelligent grammar correction service that uses the Groq Llama 3.3 70B model (FREE - 1,000 requests/day) to analyze English text and provide detailed corrections with explanations.

## Features

- ✅ Comprehensive grammar error detection
- ✅ Error categorization (tense, article, preposition, subject-verb, etc.)
- ✅ Severity classification (critical, moderate, minor)
- ✅ Position-based error highlighting
- ✅ Friendly, educational explanations
- ✅ Overall quality scoring (0-100)
- ✅ 100% FREE using Groq API

## Usage

### Python API

```python
from backend.services.grammar_guardian import GrammarGuardian

# Initialize
guardian = GrammarGuardian(api_key="your_groq_api_key")

# Analyze text
analysis = await guardian.analyze_text("I goes to school yesterday.")

# Access results
print(f"Corrected: {analysis.corrected_text}")
print(f"Score: {analysis.overall_score}/100")

for error in analysis.errors:
    print(f"{error.error_type}: {error.original_text} → {error.corrected_text}")
    print(f"Explanation: {error.explanation}")
```

### REST API

**Endpoint:** `POST /api/grammar/check`

**Request:**
```json
{
  "text": "I goes to school yesterday."
}
```

**Response:**
```json
{
  "original_text": "I goes to school yesterday.",
  "corrected_text": "I went to school yesterday.",
  "overall_score": 60.0,
  "has_errors": true,
  "errors": [
    {
      "start_pos": 2,
      "end_pos": 6,
      "error_type": "tense",
      "original_text": "goes",
      "corrected_text": "went",
      "explanation": "Use past tense 'went' because 'yesterday' indicates past time.",
      "severity": "critical"
    }
  ]
}
```

### Get Detailed Explanation

**Endpoint:** `POST /api/grammar/explain`

**Request:**
```json
{
  "error_type": "tense",
  "original": "goes",
  "corrected": "went"
}
```

**Response:**
```json
{
  "explanation": "When talking about actions in the past (indicated by 'yesterday'), we use the past tense form of verbs. 'Go' becomes 'went' in past tense."
}
```

## Error Types

The Grammar Guardian categorizes errors into these types:

- **tense**: Incorrect verb tense usage
- **article**: Missing or incorrect articles (a, an, the)
- **preposition**: Wrong preposition choice
- **subject-verb**: Subject-verb agreement errors
- **word-choice**: Incorrect word selection
- **punctuation**: Missing or incorrect punctuation
- **spelling**: Spelling mistakes

## Severity Levels

- **critical**: Major errors that significantly impact meaning
- **moderate**: Noticeable errors that should be corrected
- **minor**: Small errors or style improvements

## Configuration

Set the `GROQ_API_KEY` environment variable:

```bash
# In .env file
GROQ_API_KEY=your_groq_api_key_here
```

Get your free API key from: https://console.groq.com/

## Rate Limits

- **Groq 70B Model**: 1,000 requests per day (FREE)
- **Cost**: $0/month

## Testing

Run the test script:

```bash
python -m backend.test_grammar_guardian
```

## Implementation Details

### Position Calculation

The service calculates exact character positions for each error, enabling:
- Visual highlighting in the UI
- Precise error location identification
- Tooltip placement for explanations

### Fuzzy Matching

When the LLM returns slightly different text, the service uses fuzzy matching to find the correct position in the original text.

### Error Handling

- Returns empty errors array for perfect text
- Gracefully handles API failures
- Provides fallback responses when parsing fails

## Requirements Validation

This implementation satisfies:

- ✅ **Requirement 1.1**: Identifies and highlights grammatical errors
- ✅ **Requirement 1.2**: Provides corrections with clear explanations
- ✅ **Requirement 1.4**: Categorizes errors by type

## Next Steps

The Grammar Guardian is now ready to be integrated with:
1. Study Room frontend for real-time grammar checking
2. Conversation flow for grammar correction during chat
3. Message storage for tracking corrections over time
