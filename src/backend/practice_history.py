"""3種類の練習に共通する、追記型の履歴。教材と回答はJSONで保存する。"""

import json
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from backend.core.db_core import get_user_db_connection

PracticeKind = Literal["shadowing", "sentence_composition", "essay"]


@dataclass(frozen=True)
class Attempt:
    attempt_id: str
    user_id: str
    kind: PracticeKind
    material: dict[str, str]
    response: dict[str, str]
    retry_of: str | None = None
    created_at: str = ""


def initialize_history() -> None:
    """既存のお気に入り・習得状態を変更せず、必要なテーブルを追加する。"""
    with closing(get_user_db_connection()) as conn:
        with conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS practice_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    kind TEXT NOT NULL CHECK(kind IN ('shadowing', 'sentence_composition', 'essay')),
                    material_json TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    retry_of TEXT REFERENCES practice_attempts(attempt_id),
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS practice_attempts_user_time
                    ON practice_attempts(user_id, created_at DESC);
                CREATE TABLE IF NOT EXISTS practice_evaluations (
                    evaluation_id TEXT PRIMARY KEY,
                    attempt_id TEXT NOT NULL REFERENCES practice_attempts(attempt_id),
                    source TEXT NOT NULL,
                    model TEXT NOT NULL,
                    rubric_version TEXT NOT NULL,
                    feedback_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """
            )


def save_attempt(attempt: Attempt) -> None:
    """同一送信IDの再送は無視する。再挑戦は必ず新しいIDで保存する。"""
    if not attempt.user_id or not any(
        value.strip() for value in attempt.response.values()
    ):
        raise ValueError("ユーザーと回答が必要です。")
    with closing(get_user_db_connection()) as conn:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")
            if attempt.retry_of:
                parent = conn.execute(
                    "SELECT user_id, kind, material_json FROM practice_attempts WHERE attempt_id = ?",
                    (attempt.retry_of,),
                ).fetchone()
                expected = (attempt.user_id, attempt.kind, attempt.material)
                if (
                    parent is None
                    or (parent[0], parent[1], json.loads(parent[2])) != expected
                ):
                    raise ValueError("再挑戦元とユーザー・教材が一致しません。")
            conn.execute(
                "INSERT INTO practice_attempts VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(attempt_id) DO NOTHING",
                (
                    attempt.attempt_id,
                    attempt.user_id,
                    attempt.kind,
                    json.dumps(attempt.material, ensure_ascii=False),
                    json.dumps(attempt.response, ensure_ascii=False),
                    attempt.retry_of,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )


def list_attempts(
    user_id: str, kind: PracticeKind, limit: int = 20, offset: int = 0
) -> list[Attempt]:
    with closing(get_user_db_connection()) as conn:
        rows = conn.execute(
            "SELECT * FROM practice_attempts WHERE user_id = ? AND kind = ? ORDER BY created_at DESC, attempt_id LIMIT ? OFFSET ?",
            (user_id, kind, limit, offset),
        ).fetchall()
    return [
        Attempt(
            row["attempt_id"],
            row["user_id"],
            row["kind"],
            json.loads(row["material_json"]),
            json.loads(row["response_json"]),
            row["retry_of"],
            row["created_at"],
        )
        for row in rows
    ]


def save_self_evaluation(attempt_id: str, user_id: str, rating: str) -> None:
    if rating not in ("できた", "迷った", "できなかった"):
        raise ValueError("自己評価が不正です。")
    with closing(get_user_db_connection()) as conn:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")
            row = conn.execute(
                "SELECT 1 FROM practice_attempts WHERE attempt_id = ? AND user_id = ?",
                (attempt_id, user_id),
            ).fetchone()
            if row is None:
                raise ValueError("回答が見つかりません。")
            conn.execute(
                "INSERT INTO practice_evaluations VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid4()),
                    attempt_id,
                    "self",
                    "",
                    "self-v1",
                    json.dumps({"rating": rating}, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )


def get_self_evaluations(attempt_id: str, user_id: str) -> list[str]:
    with closing(get_user_db_connection()) as conn:
        rows = conn.execute(
            "SELECT e.feedback_json FROM practice_evaluations e JOIN practice_attempts a USING(attempt_id) "
            "WHERE a.attempt_id = ? AND a.user_id = ? AND e.source = 'self' ORDER BY e.created_at",
            (attempt_id, user_id),
        ).fetchall()
    return [str(json.loads(row[0])["rating"]) for row in rows]
