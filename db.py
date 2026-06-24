# -*- coding: utf-8 -*-
"""
ماژول مدیریت بانک اطلاعاتی SQLite.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from config import DB_PATH, DATA_DIR


DDL = """
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
    raw_dialogue_text TEXT DEFAULT '',
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
    speaker_name TEXT DEFAULT '',
    character_id INTEGER,
    text_content TEXT NOT NULL,
    audio_file_path TEXT,
    request_id TEXT,
    estimated_cost TEXT,
    cost_lookup_status TEXT NOT NULL DEFAULT 'none',
    cost_lookup_attempts INTEGER NOT NULL DEFAULT 0,
    cost_last_error TEXT DEFAULT '',
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
    lookup_status TEXT NOT NULL DEFAULT 'none',
    lookup_attempts INTEGER NOT NULL DEFAULT 0,
    lookup_error TEXT DEFAULT '',
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
"""


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path or DB_PATH)
        self._initialize()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _initialize(self):
        with self._get_connection() as conn:
            conn.executescript(DDL)
            conn.commit()
            self._run_migrations(conn)
            self._create_post_migration_indexes(conn)
            conn.commit()

    def _run_migrations(self, conn: sqlite3.Connection):
        project_cols = self._get_table_columns(conn, "projects")
        if "raw_dialogue_text" not in project_cols:
            conn.execute("ALTER TABLE projects ADD COLUMN raw_dialogue_text TEXT DEFAULT ''")

        dialogue_cols = self._get_table_columns(conn, "dialogue_lines")
        needed_dialogue_cols = {
            "speaker_name": "ALTER TABLE dialogue_lines ADD COLUMN speaker_name TEXT DEFAULT ''",
            "cost_lookup_status": "ALTER TABLE dialogue_lines ADD COLUMN cost_lookup_status TEXT NOT NULL DEFAULT 'none'",
            "cost_lookup_attempts": "ALTER TABLE dialogue_lines ADD COLUMN cost_lookup_attempts INTEGER NOT NULL DEFAULT 0",
            "cost_last_error": "ALTER TABLE dialogue_lines ADD COLUMN cost_last_error TEXT DEFAULT ''",
        }
        for col, sql in needed_dialogue_cols.items():
            if col not in dialogue_cols:
                conn.execute(sql)

        tx_cols = self._get_table_columns(conn, "transactions")
        needed_tx_cols = {
            "lookup_status": "ALTER TABLE transactions ADD COLUMN lookup_status TEXT NOT NULL DEFAULT 'none'",
            "lookup_attempts": "ALTER TABLE transactions ADD COLUMN lookup_attempts INTEGER NOT NULL DEFAULT 0",
            "lookup_error": "ALTER TABLE transactions ADD COLUMN lookup_error TEXT DEFAULT ''",
        }
        for col, sql in needed_tx_cols.items():
            if col not in tx_cols:
                conn.execute(sql)

    def _create_post_migration_indexes(self, conn: sqlite3.Connection):
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dialogue_lines_cost_lookup_status
            ON dialogue_lines(cost_lookup_status)
        """)

    def _get_table_columns(self, conn: sqlite3.Connection, table_name: str) -> List[str]:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return [row["name"] for row in rows]

    # ---------------------------------------------------------
    # تنظیمات
    # ---------------------------------------------------------
    def set_setting(self, key: str, value: str):
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO app_settings (setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key)
                DO UPDATE SET setting_value = excluded.setting_value
                """,
                (key, value),
            )
            conn.commit()

    def get_setting(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT setting_value FROM app_settings WHERE setting_key = ?",
                (key,),
            ).fetchone()
            return row["setting_value"] if row else default

    def get_all_settings(self) -> Dict[str, str]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT setting_key, setting_value FROM app_settings").fetchall()
            return {row["setting_key"]: row["setting_value"] for row in rows}

    # ---------------------------------------------------------
    # پروژه‌ها
    # ---------------------------------------------------------
    def create_project(
        self,
        title: str,
        description: str,
        language_code: str,
        audio_format: str,
        output_dir: str,
        raw_dialogue_text: str = "",
    ) -> int:
        created_at = now_str()
        updated_at = created_at

        with self._get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO projects
                (title, description, language_code, audio_format, output_dir, raw_dialogue_text, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, description, language_code, audio_format, output_dir, raw_dialogue_text, created_at, updated_at),
            )
            conn.commit()
            return cur.lastrowid

    def update_project(
        self,
        project_id: int,
        title: str,
        description: str,
        language_code: str,
        audio_format: str,
        output_dir: str,
        raw_dialogue_text: str = "",
    ):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE projects
                SET title = ?, description = ?, language_code = ?, audio_format = ?, output_dir = ?, raw_dialogue_text = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, description, language_code, audio_format, output_dir, raw_dialogue_text, now_str(), project_id),
            )
            conn.commit()

    def delete_project(self, project_id: int):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()

    def get_projects(self) -> List[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()

    def search_projects(self, keyword: str = "") -> List[sqlite3.Row]:
        with self._get_connection() as conn:
            if keyword.strip():
                pattern = f"%{keyword.strip()}%"
                return conn.execute(
                    """
                    SELECT * FROM projects
                    WHERE title LIKE ? OR description LIKE ?
                    ORDER BY id DESC
                    """,
                    (pattern, pattern),
                ).fetchall()
            return conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()

    def get_project(self, project_id: int) -> Optional[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()

    # ---------------------------------------------------------
    # شخصیت‌ها
    # ---------------------------------------------------------
    def add_character(
        self,
        project_id: int,
        name: str,
        voice_name: str,
        speed: float,
        style_note: str,
        language_code: str,
    ) -> int:
        created_at = now_str()
        updated_at = created_at

        with self._get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO characters
                (project_id, name, voice_name, speed, style_note, language_code, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, name, voice_name, speed, style_note, language_code, created_at, updated_at),
            )
            conn.commit()
            return cur.lastrowid

    def update_character(
        self,
        character_id: int,
        name: str,
        voice_name: str,
        speed: float,
        style_note: str,
        language_code: str,
    ):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE characters
                SET name = ?, voice_name = ?, speed = ?, style_note = ?, language_code = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, voice_name, speed, style_note, language_code, now_str(), character_id),
            )
            conn.commit()

    def delete_character(self, character_id: int):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))
            conn.commit()

    def get_characters_by_project(self, project_id: int) -> List[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute(
                "SELECT * FROM characters WHERE project_id = ? ORDER BY id ASC",
                (project_id,),
            ).fetchall()

    def get_character(self, character_id: int) -> Optional[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()

    def get_character_by_name(self, project_id: int, name: str) -> Optional[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute(
                """
                SELECT * FROM characters
                WHERE project_id = ? AND lower(trim(name)) = lower(trim(?))
                LIMIT 1
                """,
                (project_id, name.strip()),
            ).fetchone()

    # ---------------------------------------------------------
    # خطوط دیالوگ
    # ---------------------------------------------------------
    def clear_dialogue_lines(self, project_id: int):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM dialogue_lines WHERE project_id = ?", (project_id,))
            conn.commit()

    def add_dialogue_line(
        self,
        project_id: int,
        line_number: int,
        speaker_name: str,
        character_id: Optional[int],
        text_content: str,
        audio_file_path: str = "",
        request_id: str = "",
        estimated_cost: str = "",
        status: str = "draft",
    ) -> int:
        created_at = now_str()
        updated_at = created_at

        with self._get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO dialogue_lines
                (project_id, line_number, speaker_name, character_id, text_content, audio_file_path, request_id, estimated_cost,
                 cost_lookup_status, cost_lookup_attempts, cost_last_error, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'none', 0, '', ?, ?, ?)
                """,
                (
                    project_id,
                    line_number,
                    speaker_name,
                    character_id,
                    text_content,
                    audio_file_path,
                    request_id,
                    estimated_cost,
                    status,
                    created_at,
                    updated_at,
                ),
            )
            conn.commit()
            return cur.lastrowid

    def update_dialogue_line(
        self,
        line_id: int,
        speaker_name: str,
        character_id: Optional[int],
        text_content: str,
        audio_file_path: str,
        request_id: str,
        estimated_cost: str,
        status: str,
    ):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE dialogue_lines
                SET speaker_name = ?, character_id = ?, text_content = ?, audio_file_path = ?, request_id = ?, estimated_cost = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    speaker_name,
                    character_id,
                    text_content,
                    audio_file_path,
                    request_id,
                    estimated_cost,
                    status,
                    now_str(),
                    line_id,
                ),
            )
            conn.commit()

    def update_dialogue_line_audio(
        self,
        line_id: int,
        audio_file_path: str,
        request_id: str,
        estimated_cost: str,
        status: str,
    ):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE dialogue_lines
                SET audio_file_path = ?, request_id = ?, estimated_cost = ?, status = ?,
                    cost_lookup_status = 'pending', cost_lookup_attempts = 0, cost_last_error = '',
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    audio_file_path,
                    request_id,
                    estimated_cost,
                    status,
                    now_str(),
                    line_id,
                ),
            )
            conn.commit()

    def update_dialogue_line_cost(self, line_id: int, estimated_cost: str):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE dialogue_lines
                SET estimated_cost = ?, updated_at = ?
                WHERE id = ?
                """,
                (estimated_cost, now_str(), line_id),
            )
            conn.commit()

    def update_dialogue_line_cost_status(
        self,
        line_id: int,
        lookup_status: str,
        attempts: int,
        error_text: str = "",
    ):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE dialogue_lines
                SET cost_lookup_status = ?, cost_lookup_attempts = ?, cost_last_error = ?, updated_at = ?
                WHERE id = ?
                """,
                (lookup_status, attempts, error_text, now_str(), line_id),
            )
            conn.commit()

    def get_dialogue_lines(self, project_id: int) -> List[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute(
                """
                SELECT dl.*, c.name AS character_name, c.voice_name, c.speed
                FROM dialogue_lines dl
                LEFT JOIN characters c ON c.id = dl.character_id
                WHERE dl.project_id = ?
                ORDER BY dl.line_number ASC
                """,
                (project_id,),
            ).fetchall()

    def get_dialogue_line(self, line_id: int) -> Optional[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute(
                """
                SELECT dl.*, c.name AS character_name, c.voice_name, c.speed
                FROM dialogue_lines dl
                LEFT JOIN characters c ON c.id = dl.character_id
                WHERE dl.id = ?
                """,
                (line_id,),
            ).fetchone()

    def remap_dialogue_lines_characters(self, project_id: int):
        with self._get_connection() as conn:
            lines = conn.execute(
                "SELECT id, speaker_name, audio_file_path FROM dialogue_lines WHERE project_id = ?",
                (project_id,),
            ).fetchall()

            for line in lines:
                speaker_name = (line["speaker_name"] or "").strip()
                if not speaker_name:
                    continue

                char_row = conn.execute(
                    """
                    SELECT id FROM characters
                    WHERE project_id = ? AND lower(trim(name)) = lower(trim(?))
                    LIMIT 1
                    """,
                    (project_id, speaker_name),
                ).fetchone()

                character_id = char_row["id"] if char_row else None

                if character_id:
                    status = "generated" if (line["audio_file_path"] or "").strip() else "draft"
                else:
                    status = "no_character"

                conn.execute(
                    """
                    UPDATE dialogue_lines
                    SET character_id = ?, status = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (character_id, status, now_str(), line["id"]),
                )

            conn.commit()

    def get_modified_dialogue_lines(self, project_id: int) -> List[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute(
                """
                SELECT dl.*, c.name AS character_name, c.voice_name, c.speed
                FROM dialogue_lines dl
                LEFT JOIN characters c ON c.id = dl.character_id
                WHERE dl.project_id = ?
                  AND (dl.status = 'modified' OR dl.audio_file_path IS NULL OR dl.audio_file_path = '')
                ORDER BY dl.line_number ASC
                """,
                (project_id,),
            ).fetchall()

    def get_dialogue_lines_with_failed_cost_lookup(self, project_id: Optional[int] = None) -> List[sqlite3.Row]:
        query = """
            SELECT dl.*, c.name AS character_name, c.voice_name, c.speed
            FROM dialogue_lines dl
            LEFT JOIN characters c ON c.id = dl.character_id
            WHERE dl.request_id IS NOT NULL
              AND dl.request_id <> ''
              AND dl.cost_lookup_status IN ('pending', 'failed')
        """
        params: List[Any] = []

        if project_id:
            query += " AND dl.project_id = ?"
            params.append(project_id)

        query += " ORDER BY dl.line_number ASC"

        with self._get_connection() as conn:
            return conn.execute(query, params).fetchall()

    # ---------------------------------------------------------
    # تراکنش‌ها
    # ---------------------------------------------------------
    def add_transaction(
        self,
        project_id: Optional[int],
        dialogue_line_id: Optional[int],
        request_id: str,
        model_name: str,
        voice_name: str,
        input_text: str,
        cost_usd: str,
        cost_irr: str,
        raw_response: str,
    ) -> int:
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO transactions
                (project_id, dialogue_line_id, request_id, model_name, voice_name, input_text,
                 cost_usd, cost_irr, raw_response, lookup_status, lookup_attempts, lookup_error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'none', 0, '', ?)
                """,
                (
                    project_id,
                    dialogue_line_id,
                    request_id,
                    model_name,
                    voice_name,
                    input_text,
                    cost_usd,
                    cost_irr,
                    raw_response,
                    now_str(),
                ),
            )
            conn.commit()
            return cur.lastrowid

    def update_transaction_costs(
        self,
        request_id: str,
        cost_usd: str,
        cost_irr: str,
        raw_response: str,
    ):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE transactions
                SET cost_usd = ?, cost_irr = ?, raw_response = ?
                WHERE request_id = ?
                """,
                (cost_usd, cost_irr, raw_response, request_id),
            )
            conn.commit()

    def update_transaction_lookup_status(
        self,
        request_id: str,
        lookup_status: str,
        attempts: int,
        lookup_error: str = "",
    ):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE transactions
                SET lookup_status = ?, lookup_attempts = ?, lookup_error = ?
                WHERE request_id = ?
                """,
                (lookup_status, attempts, lookup_error, request_id),
            )
            conn.commit()

    def get_transactions(self, project_id: Optional[int] = None, request_id: str = "") -> List[sqlite3.Row]:
        query = """
            SELECT
                t.*,
                p.title AS project_title,
                dl.line_number
            FROM transactions t
            LEFT JOIN projects p ON p.id = t.project_id
            LEFT JOIN dialogue_lines dl ON dl.id = t.dialogue_line_id
            WHERE 1=1
        """
        params: List[Any] = []

        if project_id:
            query += " AND t.project_id = ?"
            params.append(project_id)

        if request_id.strip():
            query += " AND t.request_id LIKE ?"
            params.append(f"%{request_id.strip()}%")

        query += " ORDER BY t.id DESC"

        with self._get_connection() as conn:
            return conn.execute(query, params).fetchall()