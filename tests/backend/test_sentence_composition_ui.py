"""一時DBで瞬間英作文の画面操作を検証する。"""

# Streamlit ElementList の動的な要素型を pylint は推論できない。
# pylint: disable=no-member

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from backend.practice_history import list_attempts


class CompositionUITests(unittest.TestCase):
    def test_save_restart_and_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ, {"USER_DB_PATH": str(Path(directory) / "user.db")}
            ):
                app = AppTest.from_string(
                    "from frontend.tab8_sentence_composition import render\nrender('test-user')"
                )
                app.run()
                self.assertFalse(app.exception)
                app.text_area[0].input("I drink coffee every morning.")
                app.button[1].click().run()
                self.assertFalse(app.exception)
                self.assertTrue(app.text_area[0].disabled)
                attempts = list_attempts("test-user", "sentence_composition")
                self.assertEqual(len(attempts), 1)
                app = AppTest.from_string(
                    "from frontend.tab8_sentence_composition import render\nrender('test-user')"
                )
                app.run()
                app.button(
                    key="composition_retry_" + attempts[0].attempt_id
                ).click().run()
                self.assertEqual(app.text_area[0].value, "")
                self.assertFalse(app.text_area[0].disabled)
                app.text_area[0].input("Every morning, I drink coffee.")
                app.button[1].click().run()
                self.assertFalse(app.exception)
                attempts = list_attempts("test-user", "sentence_composition")
                self.assertEqual(len(attempts), 2)
                self.assertEqual(attempts[0].retry_of, attempts[1].attempt_id)
