from __future__ import annotations

import sqlite3
from models import SchoolNotice

DB_PATH = "notice.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            hash     TEXT PRIMARY KEY,
            title    TEXT NOT NULL,
            url      TEXT NOT NULL,
            content  TEXT,
            category TEXT,
            date     TEXT
        )
    """)
    # 기존 DB에 category 컬럼이 없으면 추가
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(notices)")}
    if "category" not in existing:
        cursor.execute("ALTER TABLE notices ADD COLUMN category TEXT")
    conn.commit()
    conn.close()


def save_to_db(docs: list[SchoolNotice]) -> int:
    """저장된 신규 문서 수를 반환."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    inserted = 0

    for doc in docs:
        cursor.execute(
            """
            INSERT OR IGNORE INTO notices (hash, title, url, content, category, date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                doc.hash,
                doc.title,
                doc.url,
                doc.text,
                doc.metadata.get("category", "일반"),
                doc.metadata.get("published_at", ""),
            ),
        )
        inserted += cursor.rowcount

    conn.commit()
    conn.close()
    return inserted


def search_notices(query: str, category: str | None = None, limit: int = 10) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    like = f"%{query}%"

    if category:
        cursor.execute(
            """
            SELECT title, url, content, category, date FROM notices
            WHERE (title LIKE ? OR content LIKE ?) AND category = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (like, like, category, limit),
        )
    else:
        cursor.execute(
            """
            SELECT title, url, content, category, date FROM notices
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (like, like, limit),
        )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_notice_count() -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notices")
    count = cursor.fetchone()[0]
    conn.close()
    return count
