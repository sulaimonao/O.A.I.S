-- Schema for the conversation history
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    model TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Schema for the user profiles
CREATE TABLE user_profiles (
    session_id TEXT PRIMARY KEY,
    name TEXT
);
