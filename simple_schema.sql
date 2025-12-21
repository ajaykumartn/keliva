-- KeLiva Simplified Database Schema
-- Only includes essential features: Grammar Check, Voice Practice, Telegram/WhatsApp

-- Users table (simplified)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    session_id TEXT UNIQUE,
    name TEXT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    preferred_language TEXT DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    full_name TEXT,
    password_hash TEXT DEFAULT ''
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    interface TEXT DEFAULT 'telegram', -- telegram, whatsapp, web
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    role TEXT CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    message_type TEXT DEFAULT 'text', -- text, voice
    metadata TEXT, -- JSON for additional data
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Grammar corrections table
CREATE TABLE IF NOT EXISTS grammar_corrections (
    id TEXT PRIMARY KEY,
    message_id TEXT,
    original_text TEXT NOT NULL,
    corrected_text TEXT NOT NULL,
    errors TEXT, -- JSON array of error details
    score INTEGER DEFAULT 0, -- Grammar score 0-100
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id)
);

-- Voice practice sessions table
CREATE TABLE IF NOT EXISTS voice_practice_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    text_to_read TEXT NOT NULL,
    audio_url TEXT,
    pronunciation_score INTEGER DEFAULT 0, -- 0-100
    feedback TEXT, -- JSON with detailed feedback
    duration_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User facts table (for personalization - minimal)
CREATE TABLE IF NOT EXISTS user_facts (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    fact_text TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_session ON users(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_grammar_message ON grammar_corrections(message_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_user ON voice_practice_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_facts_user ON user_facts(user_id);