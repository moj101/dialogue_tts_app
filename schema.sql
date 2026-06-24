PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    language_code TEXT NOT NULL DEFAULT 'fr',
    audio_format TEXT NOT NULL DEFAULT 'mp3',
    output_dir TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    voice_name TEXT NOT NULL,
    speed REAL NOT NULL DEFAULT 1.0,
    style_note TEXT,
    language_code TEXT NOT NULL DEFAULT 'fr',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dialogue_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    character_id INTEGER,
    text_content TEXT NOT NULL,
    audio_file_path TEXT,
    request_id TEXT,
    estimated_cost TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    dialogue_line_id INTEGER,
    request_id TEXT,
    model_name TEXT,
    voice_name TEXT,
    input_text TEXT,
    cost_usd TEXT,
    cost_irr TEXT,
    raw_response TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY(dialogue_line_id) REFERENCES dialogue_lines(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_characters_project_id
ON characters(project_id);

CREATE INDEX IF NOT EXISTS idx_dialogue_lines_project_id
ON dialogue_lines(project_id);

CREATE INDEX IF NOT EXISTS idx_dialogue_lines_character_id
ON dialogue_lines(character_id);

CREATE INDEX IF NOT EXISTS idx_transactions_project_id
ON transactions(project_id);

CREATE INDEX IF NOT EXISTS idx_transactions_dialogue_line_id
ON transactions(dialogue_line_id);

CREATE INDEX IF NOT EXISTS idx_transactions_request_id
ON transactions(request_id);