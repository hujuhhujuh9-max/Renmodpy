import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from renmodpy.board_session import BoardSession
from renmodpy.records import RecordStore, RecordsError


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "records.json"
        self.records = RecordStore(self.path)

    def test_create_update_delete_survive_fresh_store(self):
        identifier = self.records.create({"title": "灯台", "body": "A note"})
        again = RecordStore(self.path)
        self.assertEqual(again.list()[0]["id"], identifier)
        revision = again.snapshot()["revision"]
        again.update(identifier, {"title": "Edited"}, expected_revision=revision)
        self.assertEqual(self.records.list()[0]["values"], {"title": "Edited"})
        self.records.delete(identifier)
        self.assertEqual(RecordStore(self.path).list(), [])

    def test_loading_old_story_snapshot_keeps_newer_records(self):
        board = BoardSession()
        old_story = pickle.dumps(board)
        self.records.create({"title": "Newer application data"})
        restored = pickle.loads(old_story)
        self.assertEqual(restored.snapshot(), board.snapshot())
        self.assertEqual(RecordStore(self.path).list()[0]["values"]["title"],
                         "Newer application data")

    def test_stale_edit_and_delete_preserve_current_file(self):
        identifier = self.records.create({"title": "Original"})
        stale_revision = self.records.snapshot()["revision"]
        self.records.create({"title": "Newer"})
        before = self.path.read_bytes()
        for action in (
            lambda: self.records.update(identifier, {"title": "Old"}, expected_revision=stale_revision),
            lambda: self.records.delete(identifier, expected_revision=stale_revision),
        ):
            with self.assertRaises(RecordsError):
                action()
            self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_or_future_file_is_never_overwritten(self):
        for value in ("invalid JSON", '{"version": 2, "revision": 0, "records": []}'):
            with self.subTest(value=value):
                self.path.write_text(value)
                with self.assertRaises(RecordsError):
                    self.records.create({"title": "Replacement"})
                self.assertEqual(self.path.read_text(), value)

    def test_failed_atomic_replace_preserves_previous_records_and_cleans_temp(self):
        self.records.create({"title": "Original"})
        before = self.path.read_bytes()
        with patch("renmodpy.records.os.replace", side_effect=OSError("disk unavailable")):
            with self.assertRaises(RecordsError):
                self.records.create({"title": "Lost write"})
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_snapshots_are_private_copies(self):
        self.records.create({"title": "Original"})
        snapshot = self.records.snapshot()
        snapshot["records"][0]["values"]["title"] = "Changed in memory"
        self.assertEqual(self.records.list()[0]["values"]["title"], "Original")

    def test_unwritable_directory_is_reported_as_a_records_error(self):
        with patch("renmodpy.records.Path.mkdir", side_effect=OSError("unwritable")):
            with self.assertRaises(RecordsError):
                self.records.create({"title": "Cannot write"})
        self.assertFalse(self.path.exists())

    def test_duplicate_identity_is_rejected(self):
        identifier = self.records.create({"title": "Original"})
        data = self.records.snapshot()
        data["records"].append(data["records"][0])
        self.path.write_text(json.dumps(data))
        with self.assertRaises(RecordsError):
            self.records.delete(identifier)
