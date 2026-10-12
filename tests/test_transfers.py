import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from renmodpy import RecordStore, RecordsError
from renmodpy.transfers import dump_records, load_records, preview_records


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = RecordStore(Path(self.directory.name) / "records.json")
        self.identifier = self.store.create({"title": "Blåbær", "body": "Café Ω\nLiteral {note} [value]", "hidden": "keep"})

    def test_backup_round_trip_keeps_identity_unicode_and_hidden_fields(self):
        snapshot = self.store.snapshot()
        text = dump_records(snapshot)
        self.assertIn("Blåbær", text)
        self.assertNotIn("revision", text)
        self.assertEqual(load_records(text), snapshot["records"])

    def test_preview_never_mutates_and_merge_keeps_omitted_records_and_fields(self):
        other = self.store.create({"title": "Unrelated"})
        before = self.store.path.read_bytes()
        rows = [{"id": self.identifier, "values": {"title": "Updated"}},
                {"id": "a" * 32, "values": {"title": "New"}}]
        preview = preview_records(rows, self.store.snapshot())
        self.assertEqual((preview["new"], preview["updated"], preview["unchanged"]), (1, 1, 0))
        self.assertEqual(self.store.path.read_bytes(), before)
        merged = self.store.merge(rows, expected_revision=preview["revision"])
        indexed = {r["id"]: r["values"] for r in merged["records"]}
        self.assertEqual(indexed[self.identifier]["hidden"], "keep")
        self.assertEqual(indexed[self.identifier]["title"], "Updated")
        self.assertEqual(indexed[other]["title"], "Unrelated")

    def test_stale_import_preserves_latest_records(self):
        snapshot = self.store.snapshot()
        self.store.update(self.identifier, {"title": "Latest"})
        before = self.store.path.read_bytes()
        with self.assertRaises(RecordsError):
            self.store.merge(snapshot["records"], expected_revision=snapshot["revision"])
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_malformed_or_unsupported_backups_are_rejected_without_writes(self):
        valid = json.loads(dump_records(self.store.snapshot()))
        cases = ["not JSON", json.dumps(dict(valid, version=True)), json.dumps(dict(valid, version=2)),
                 json.dumps(dict(valid, records=valid["records"] * 2)),
                 json.dumps(dict(valid, records=[{"id": "a" * 32, "values": {"body": "null\0value"}}]))]
        before = self.store.path.read_bytes()
        for text in cases:
            with self.assertRaises(ValueError):
                load_records(text)
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_import_capacity_and_combined_field_limits_are_atomic(self):
        # Each imported row is valid by itself, but merging its fields can
        # exceed the schema limit. Earlier edits in that batch must not persist.
        full = self.store.create({str(i): "value" for i in range(32)})
        rows = [{"id": self.identifier, "values": {"title": "Should not persist"}},
                {"id": full, "values": {"new": "extra"}}]
        before = self.store.path.read_bytes()
        with self.assertRaises(ValueError):
            self.store.merge(rows, expected_revision=self.store.snapshot()["revision"])
        self.assertEqual(self.store.path.read_bytes(), before)
        snapshot = {"revision": 1, "records": [{"id": f"{i:032x}", "values": {"title": "row"}} for i in range(1000)]}
        with self.assertRaises(ValueError):
            preview_records([{"id": "f" * 32, "values": {"title": "new"}}], snapshot)

    def test_failed_import_write_preserves_original_bytes(self):
        before = self.store.path.read_bytes()
        with patch("renmodpy.records.os.replace", side_effect=OSError("full disk")):
            with self.assertRaises(RecordsError):
                self.store.merge([{"id": self.identifier, "values": {"title": "Not saved"}}],
                                 expected_revision=self.store.snapshot()["revision"])
        self.assertEqual(self.store.path.read_bytes(), before)
