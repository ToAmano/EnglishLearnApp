"""実DBを変更せず、保存・再挑戦・評価の永続化を確認する。"""

import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from backend.practice_history import (
    Attempt,
    get_self_evaluations,
    initialize_history,
    list_attempts,
    save_attempt,
    save_self_evaluation,
)
from backend.practice_materials import get_sentence_materials


class HistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        # addCleanup で一時ディレクトリを確実に解放する。
        # pylint: disable=consider-using-with
        self.directory = (
            tempfile.TemporaryDirectory()
        )  # pylint: disable=consider-using-with
        self.addCleanup(self.directory.cleanup)
        self.db_path = str(Path(self.directory.name) / "user.db")
        environment = patch.dict(os.environ, {"USER_DB_PATH": self.db_path})
        environment.start()
        self.addCleanup(environment.stop)
        initialize_history()
        self.attempt = Attempt(
            "first",
            "default_user",
            "sentence_composition",
            get_sentence_materials()[0],
            {"text": "My answer"},
        )

    def test_retry_preserves_original_and_snapshot(self) -> None:
        save_attempt(self.attempt)
        save_attempt(
            replace(
                self.attempt,
                attempt_id="second",
                retry_of="first",
                response={"text": "Better answer"},
            )
        )
        self.attempt.material["prompt"] = "changed source"
        initialize_history()
        attempts = list_attempts("default_user", "sentence_composition")
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0].retry_of, "first")
        self.assertEqual(attempts[1].response["text"], "My answer")
        self.assertNotEqual(attempts[1].material["prompt"], "changed source")

    def test_idempotency_and_user_isolation(self) -> None:
        save_attempt(self.attempt)
        save_attempt(self.attempt)
        self.assertEqual(len(list_attempts("default_user", "sentence_composition")), 1)
        self.assertEqual(list_attempts("another", "sentence_composition"), [])
        with self.assertRaises(ValueError):
            save_attempt(
                replace(
                    self.attempt,
                    attempt_id="other",
                    user_id="another",
                    retry_of="first",
                )
            )

    def test_empty_response_and_missing_parent_rejected(self) -> None:
        with self.assertRaises(ValueError):
            save_attempt(replace(self.attempt, response={"text": "  "}))
        with self.assertRaises(ValueError):
            save_attempt(replace(self.attempt, retry_of="missing"))

    def test_evaluations_are_append_only(self) -> None:
        save_attempt(self.attempt)
        save_self_evaluation("first", "default_user", "迷った")
        save_self_evaluation("first", "default_user", "できた")
        self.assertEqual(
            get_self_evaluations("first", "default_user"), ["迷った", "できた"]
        )
        self.assertEqual(get_self_evaluations("first", "other"), [])

    def test_other_modes_and_existing_tables(self) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute("CREATE TABLE favorites (word TEXT PRIMARY KEY)")
                conn.execute("INSERT INTO favorites VALUES ('hello')")
        initialize_history()
        save_attempt(
            replace(
                self.attempt,
                kind="shadowing",
                response={"audio_path": "recordings/example.wav"},
            )
        )
        save_attempt(replace(self.attempt, attempt_id="essay", kind="essay"))
        self.assertEqual(len(list_attempts("default_user", "shadowing")), 1)
        self.assertEqual(len(list_attempts("default_user", "essay")), 1)
        with closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                self.assertEqual(
                    conn.execute("SELECT word FROM favorites").fetchone()[0], "hello"
                )


if __name__ == "__main__":
    unittest.main()
