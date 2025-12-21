-- KeLiva Database Schema for Cloudflare D1

-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    session_id TEXT UNIQUE,
    name TEXT,
    username TEXT UNIQUE,
    full_name TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    profile_picture TEXT,
    preferred_language TEXT DEFAULT 'en',
    family_group_id TEXT,
    learning_streak INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (family_group_id) REFERENCES family_groups(id)
);

-- Conversations table
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    interface TEXT DEFAULT 'telegram',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Messages table
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    role TEXT CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    message_type TEXT DEFAULT 'text',
    metadata TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Grammar corrections table
CREATE TABLE grammar_corrections (
    id TEXT PRIMARY KEY,
    message_id TEXT,
    original_text TEXT NOT NULL,
    corrected_text TEXT NOT NULL,
    errors TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id)
);

-- User facts table (for personalization)
CREATE TABLE user_facts (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    fact_text TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Family Groups table
CREATE TABLE family_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    members TEXT NOT NULL, -- JSON array of member IDs
    group_settings TEXT DEFAULT '{}', -- JSON settings
    is_active INTEGER DEFAULT 1,
    group_avatar TEXT,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Family Chat Messages table
CREATE TABLE family_chat_messages (
    id TEXT PRIMARY KEY,
    family_group_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    message_text TEXT,
    message_type TEXT DEFAULT 'text', -- text, voice, video, image, file, system
    voice_url TEXT,
    video_url TEXT,
    image_url TEXT,
    file_url TEXT,
    emotion_detected TEXT,
    reply_to_message_id TEXT,
    is_edited INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP,
    FOREIGN KEY (family_group_id) REFERENCES family_groups(id),
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (reply_to_message_id) REFERENCES family_chat_messages(id)
);

-- Family Group Invitations table
CREATE TABLE family_group_invitations (
    id TEXT PRIMARY KEY,
    group_id TEXT NOT NULL,
    invited_by TEXT NOT NULL,
    invited_user_email TEXT,
    invited_user_phone TEXT,
    invitation_code TEXT UNIQUE,
    status TEXT DEFAULT 'pending', -- pending, accepted, declined, expired
    is_used INTEGER DEFAULT 0,
    used_by TEXT,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES family_groups(id),
    FOREIGN KEY (invited_by) REFERENCES users(id),
    FOREIGN KEY (used_by) REFERENCES users(id)
);

-- Family Learning Progress table
CREATE TABLE family_learning_progress (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    activity_type TEXT NOT NULL, -- vocabulary, grammar, conversation, etc.
    progress_data TEXT, -- JSON data
    points_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (group_id) REFERENCES family_groups(id)
);

-- Indexes for performance
CREATE INDEX idx_users_telegram ON users(telegram_id);
CREATE INDEX idx_users_session ON users(session_id);
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_grammar_message ON grammar_corrections(message_id);
CREATE INDEX idx_facts_user ON user_facts(user_id);
CREATE INDEX idx_family_groups_created_by ON family_groups(created_by);
CREATE INDEX idx_family_chat_group ON family_chat_messages(family_group_id);
CREATE INDEX idx_family_chat_sender ON family_chat_messages(sender_id);
CREATE INDEX idx_family_chat_timestamp ON family_chat_messages(created_at);
CREATE INDEX idx_family_invitations_group ON family_group_invitations(group_id);
CREATE INDEX idx_family_invitations_code ON family_group_invitations(invitation_code);
CREATE INDEX idx_family_progress_user ON family_learning_progress(user_id);
CREATE INDEX idx_family_progress_group ON family_learning_progress(group_id);
