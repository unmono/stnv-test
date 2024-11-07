-- users table
CREATE TABLE IF NOT EXISTS users (
    email TEXT NOT NULL,
    hash TEXT NOT NULL,
    autoreply_timeout INTEGER
);
CREATE UNIQUE INDEX IF NOT EXISTS email_index
ON users(email);

-- posts table
CREATE TABLE IF NOT EXISTS posts (
    author_id INTEGER REFERENCES users(rowid) ON DELETE SET NULL,
    title TEXT,
    body TEXT,
    created_at TEXT NOT NULL DEFAULT current_timestamp,
    updated_at TEXT NOT NULL DEFAULT current_timestamp
);
CREATE TRIGGER posts_updated_at
AFTER UPDATE ON posts
WHEN old.updated_at <> current_timestamp
BEGIN
    UPDATE posts
    SET updated_at = current_timestamp
    WHERE rowid = old.rowid;
END;

-- comments table
CREATE TABLE comments(
    author_id INTEGER REFERENCES users(rowid) ON DELETE SET NULL,
    reply_to INTEGER REFERENCES comments(rowid) ON DELETE SET NULL,
    post_id INTEGER REFERENCES posts(rowid) ON DELETE SET NULL,
    body TEXT NOT NULL,
    status INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT current_timestamp,
    updated_at TEXT NOT NULL DEFAULT current_timestamp,
    autoreply_at INTEGER
);

CREATE INDEX IF NOT EXISTS autoreply_index
ON comments(autoreply_at);

CREATE TRIGGER comments_updated_at
AFTER UPDATE ON comments
WHEN old.updated_at <> current_timestamp
BEGIN
    UPDATE comments
    SET updated_at = current_timestamp
    WHERE rowid = old.rowid;
END;
