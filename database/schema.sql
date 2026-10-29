CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    handle TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    username_last_changed TEXT,
    username_change_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    theory_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_members_handle ON members(handle);
