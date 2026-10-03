"""別タブに同じ単語を表示しても、操作をユーザー別に保存する。"""

from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from backend.favorite import get_favorites_words
from backend.users import get_or_create_google_user
from backend.vocab_status import get_vocab_status


def test_shared_widgets_use_tab_and_user_keys(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"USER_DB_PATH": str(tmp_path / "user.db")}):
        first = get_or_create_google_user("first")
        second = get_or_create_google_user("second")
        script = (
            "from frontend.core import show_favorite, show_status\n"
            f"show_favorite('hello', 'search', '{first}')\n"
            f"show_favorite('hello', 'card', '{first}')\n"
            f"show_status('hello', 'search', '{first}')\n"
            f"show_status('hello', 'card', '{first}')"
        )
        app = AppTest.from_string(script).run()
        assert not app.exception
        app.button[0].click().run()
        assert not app.exception
        assert get_favorites_words(first) == ["hello"]
        assert get_favorites_words(second) == []
        app.selectbox[0].select("active").run()
        assert not app.exception
        assert get_vocab_status("hello", first) == "active"
        assert get_vocab_status("hello", second) == "unknown"


def test_status_callback_reports_database_failure(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"USER_DB_PATH": str(tmp_path / "user.db")}):
        account = get_or_create_google_user("first")
        script = f"from frontend.core import show_status\nshow_status('hello', 'search', '{account}')"
        app = AppTest.from_string(script).run()
        assert not app.exception
        with patch.dict(
            "os.environ", {"USER_DB_PATH": str(tmp_path / "missing" / "user.db")}
        ):
            app.selectbox[0].select("active").run()
        assert not app.exception
        assert app.error
