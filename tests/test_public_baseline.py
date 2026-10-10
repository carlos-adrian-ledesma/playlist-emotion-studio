"""Regression guard for the public Playlist Emotion Studio SQLite baseline.

This test suite uses only Python's standard library. It checks the committed
sample database, not a user's working database or external service accounts.
"""

from contextlib import closing
from pathlib import Path
import sqlite3
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_DB = PROJECT_ROOT / "data" / "playlist.db"
SENSITIVE_SETTING_MARKERS = (
    "password",
    "secret",
    "access_token",
    "refresh_token",
    "api_key",
    "client_id",
    "credential",
)


class PublicBaselineTests(unittest.TestCase):
    """Catch accidental publication of runtime records or credentials."""

    def setUp(self):
        self.assertTrue(BASELINE_DB.is_file(), f"Missing public baseline: {BASELINE_DB}")

    def _connect(self):
        # Open the committed baseline read-only; never modify it during tests.
        return sqlite3.connect(BASELINE_DB.resolve().as_uri() + "?mode=ro", uri=True)

    def test_sqlite_integrity(self):
        with closing(self._connect()) as db:
            result = db.execute("PRAGMA integrity_check").fetchone()[0]
            self.assertEqual(result, "ok", f"SQLite integrity check failed: {result}")

    def test_operational_tables_are_empty(self):
        with closing(self._connect()) as db:
            names = [
                name for (name,) in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ) if not name.startswith("sqlite_")
            ]
            for required in ("settings", "songs", "setlists", "setlist_items"):
                self.assertIn(required, names, f"Expected table missing: {required}")
            for name in names:
                if name == "settings":
                    continue  # Allowed to contain non-sensitive app defaults.
                escaped = name.replace('"', '""')
                count = db.execute(f'SELECT COUNT(*) FROM "{escaped}"').fetchone()[0]
                self.assertEqual(count, 0, f"Public database contains {count} rows in {name}")

    def test_no_integration_credentials(self):
        with closing(self._connect()) as db:
            settings = dict(db.execute("SELECT key, value FROM settings").fetchall())
            for key in (
                "youtube_api_key",
                "spotify_client_id",
                "spotify_access_token",
                "spotify_refresh_token",
            ):
                self.assertIn(key, settings, f"Expected setting missing: {key}")
                self.assertEqual(settings[key], "", f"Public database includes {key}")
            self.assertEqual(settings.get("spotify_token_expires_at"), "0")
            for key, value in settings.items():
                if any(marker in key.lower() for marker in SENSITIVE_SETTING_MARKERS):
                    self.assertIn(
                        str(value or ""), ("", "0"),
                        f"Sensitive setting must not be committed: {key}",
                    )

    def test_only_one_committed_sqlite_database(self):
        data_dir = BASELINE_DB.parent
        databases = sorted(
            p.relative_to(PROJECT_ROOT).as_posix()
            for p in data_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in (".db", ".sqlite", ".sqlite3")
        )
        self.assertEqual(databases, ["data/playlist.db"])


if __name__ == "__main__":
    unittest.main()
