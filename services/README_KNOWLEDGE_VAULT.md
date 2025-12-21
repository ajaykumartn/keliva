# Knowledge Vault Service

## Overview

The Knowledge Vault is a RAG (Retrieval-Augmented Generation) based long-term memory system that stores and retrieves personal context about users. It enables KeLiva to remember personal details, relationships, and conversation history across sessions.

## Features

- **Fact Extraction**: Automatically extracts personal information from conversations using Groq LLM
- **Vector Storage**: Uses ChromaDB with sentence-transformers for semantic search
- **Context Retrieval**: Retrieves relevant facts based on current conversation
- **Entity Relationships**: Builds and queries relationship graphs between entities
- **Persistent Memory**: Maintains user context across sessions and devices

## Architecture

```
User Message
    ↓
Fact Extraction (Groq 70B)
    ↓
Structured Facts (Entity, Relation, Attribute, Value)
    ↓
Vector Embedding (sentence-transformers)
    ↓
ChromaDB Storage
    ↓
Semantic Search (top-k=5)
    ↓
Context Injection into LLM Prompt
```

## Data Structures

### Fact

Represents a personal fact about the user:

```python
@dataclass
class Fact:
    id: str                    # Unique identifier
    user_id: str              # User identifier
    entity: str               # "Abhishek", "Mom", "Robotics Project"
    relation: str             # "friend", "family", "project"
    attribute: str            # "annoying", "health issue", "deadline"
    value: str                # "today", "recovering", "next week"
    context: str              # Full sentence where fact was mentioned
    timestamp: datetime       # When fact was extracted
    embedding: List[float]    # Vector embedding (optional)
```

### EntityGraph

Represents relationship graph for a specific entity:

```python
@dataclass
class EntityGraph:
    entity: str                              # Entity name
    relationships: Dict[str, List[str]]      # relation_type -> [related_entities]
    attributes: Dict[str, str]               # attribute_name -> value
```

## Usage

### Initialize Knowledge Vault

```python
from services.knowledge_vault import KnowledgeVault

vault = KnowledgeVault(
    api_key="your-groq-api-key",  # Optional, defaults to GROQ_API_KEY env var
    persist_directory="./chroma_db"  # Where to store ChromaDB data
)
```

### Extract Facts from Conversation

```python
# Extract facts from user message
facts = await vault.extract_facts(
    user_id="user_123",
    message="My friend Abhishek is working on a robotics project.",
    conversation_history=[  # Optional context
        {"role": "user", "content": "I'm stressed about exams"},
        {"role": "assistant", "content": "What subject?"}
    ]
)

# Store extracted facts
for fact in facts:
    await vault.store_fact(fact)
```

### Retrieve Context for Response Generation

```python
# Retrieve relevant facts for current conversation
relevant_facts = await vault.retrieve_context(
    query="Tell me about Abhishek",
    user_id="user_123",
    top_k=5  # Number of facts to retrieve
)

# Format facts for LLM prompt
context_string = "\n".join([
    f"- {fact.entity}: {fact.attribute} = {fact.value}"
    for fact in relevant_facts
])
```

### Query Entity Relationships

```python
# Get relationship graph for specific entity
graph = await vault.get_entity_relationships(
    entity_name="Abhishek",
    user_id="user_123"
)

print(f"Relationships: {graph.relationships}")
# Output: {"friend": ["user"], "project": ["robotics"]}

print(f"Attributes: {graph.attributes}")
# Output: {"occupation": "robotics", "personality": "annoying but brilliant"}
```

### Manage Facts

```python
# Get all facts for a user
all_facts = vault.get_all_facts("user_123", limit=100)

# Delete a specific fact
vault.delete_fact(fact_id="fact_uuid")

# Clear all facts for a user
vault.clear_user_facts("user_123")
```

## Integration with Conversation Flow

### Step 1: Extract Facts After User Message

```python
# After receiving user message
user_message = "My mom is recovering from surgery"

# Extract and store facts
facts = await vault.extract_facts(user_id, user_message)
for fact in facts:
    await vault.store_fact(fact)
```

### Step 2: Retrieve Context Before Response Generation

```python
# Before generating response
relevant_context = await vault.retrieve_context(
    query=user_message,
    user_id=user_id,
    top_k=5
)

# Format context for LLM prompt
context_text = "KNOWLEDGE ABOUT USER:\n"
for fact in relevant_context:
    context_text += f"- {fact.context}\n"
```

### Step 3: Inject Context into LLM Prompt

```python
system_prompt = f"""You are Vani, the user's best friend.

{context_text}

Respond naturally using this context."""

# Generate response with context
response = await llm.generate(system_prompt, user_message)
```

## Fact Extraction Examples

### Example 1: Personal Relationships

**Input**: "My friend Abhishek is really annoying but he's brilliant at coding."

**Extracted Facts**:
```python
[
    Fact(
        entity="Abhishek",
        relation="friend",
        attribute="personality",
        value="annoying but brilliant",
        context="My friend Abhishek is really annoying but he's brilliant at coding."
    ),
    Fact(
        entity="Abhishek",
        relation="friend",
        attribute="skill",
        value="coding",
        context="My friend Abhishek is really annoying but he's brilliant at coding."
    )
]
```

### Example 2: Family Information

**Input**: "My mom is recovering from her surgery. She's feeling much better now."

**Extracted Facts**:
```python
[
    Fact(
        entity="Mom",
        relation="family",
        attribute="health",
        value="recovering from surgery",
        context="My mom is recovering from her surgery."
    ),
    Fact(
        entity="Mom",
        relation="family",
        attribute="status",
        value="feeling much better",
        context="She's feeling much better now."
    )
]
```

### Example 3: Projects and Events

**Input**: "I have a physics exam next week. Dr. Sharma is very strict about deadlines."

**Extracted Facts**:
```python
[
    Fact(
        entity="Physics Exam",
        relation="event",
        attribute="deadline",
        value="next week",
        context="I have a physics exam next week."
    ),
    Fact(
        entity="Dr. Sharma",
        relation="professor",
        attribute="personality",
        value="strict about deadlines",
        context="Dr. Sharma is very strict about deadlines."
    )
]
```

## Semantic Search Examples

### Query: "Tell me about Abhishek"

**Retrieved Facts** (ranked by relevance):
1. "Abhishek is my friend who works on robotics projects"
2. "Abhishek is brilliant at coding"
3. "Abhishek loves playing chess"

### Query: "How is my family doing?"

**Retrieved Facts**:
1. "Mom is recovering from surgery"
2. "Mom is feeling much better now"
3. "Dad is traveling for work this week"

## Configuration

### Environment Variables

```bash
# Required
GROQ_API_KEY=your-groq-api-key-here

# Optional
CHROMA_DB_PATH=./chroma_db  # Default persist directory
```

### ChromaDB Settings

The Knowledge Vault uses:
- **Embedding Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Collection Name**: `user_facts`
- **Persistence**: Local directory (configurable)

### LLM Settings

- **Model**: Groq Llama 3.3 70B (for better fact extraction)
- **Temperature**: 0.2 (low for consistent extraction)
- **Max Tokens**: 1000

## Testing

Run the comprehensive test suite:

```bash
cd backend
python test_knowledge_vault.py
```

Tests cover:
- Fact extraction from various message types
- Storage and retrieval
- Semantic search accuracy
- Entity relationship graphs
- Edge cases and error handling
- Multilingual/code-mixed messages

## Performance Considerations

### Embedding Generation

- Uses `all-MiniLM-L6-v2` (384 dimensions)
- Fast inference (~10ms per embedding)
- Suitable for real-time applications

### Storage

- ChromaDB uses SQLite backend
- Efficient for up to 1M+ facts
- Automatic indexing for fast retrieval

### Retrieval Speed

- Semantic search: ~20-50ms for top-5 results
- Scales well with user base
- Consider sharding by user_id for large deployments

## Best Practices

### 1. Extract Facts After Every User Message

```python
# Always extract facts to build comprehensive memory
facts = await vault.extract_facts(user_id, message)
for fact in facts:
    await vault.store_fact(fact)
```

### 2. Retrieve Context Before Response Generation

```python
# Always retrieve context for personalized responses
context = await vault.retrieve_context(message, user_id, top_k=5)
```

### 3. Use Conversation History for Better Extraction

```python
# Provide recent conversation for context-aware extraction
facts = await vault.extract_facts(
    user_id,
    message,
    conversation_history=recent_messages[-3:]  # Last 3 messages
)
```

### 4. Monitor Storage Growth

```python
# Periodically check fact count
all_facts = vault.get_all_facts(user_id)
if len(all_facts) > 1000:
    # Consider archiving or pruning old facts
    pass
```

## Troubleshooting

### Issue: No facts extracted

**Possible causes**:
- Message contains no personal information
- LLM API error
- Incorrect API key

**Solution**: Check logs and verify GROQ_API_KEY

### Issue: Irrelevant facts retrieved

**Possible causes**:
- Query too generic
- Insufficient facts stored
- Embedding model mismatch

**Solution**: Increase top_k or refine query

### Issue: ChromaDB persistence errors

**Possible causes**:
- Insufficient disk space
- Permission issues
- Corrupted database

**Solution**: Check disk space and permissions, recreate database if needed

## Future Enhancements

- [ ] Fact deduplication (merge similar facts)
- [ ] Temporal reasoning (track changes over time)
- [ ] Fact importance scoring (prioritize recent/important facts)
- [ ] Multi-modal facts (images, audio references)
- [ ] Fact verification (cross-reference with external sources)
- [ ] Privacy controls (user-controlled fact deletion)

## Requirements Validation

This implementation satisfies:

- **Requirement 4.1**: Extracts and stores personal facts with entity and relation metadata ✓
- **Requirement 4.2**: Retrieves relevant context before generating responses ✓
- **Requirement 4.4**: Maintains entity relationship graphs ✓
- **Requirement 4.5**: Persists context across sessions ✓
- **Requirement 9.3**: Stores facts in persistent database ✓
- **Requirement 9.4**: Maintains continuity over time ✓
