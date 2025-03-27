-- Create a table to store messages
CREATE TABLE IF NOT EXISTS discord_messages (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    server_info TEXT
);
