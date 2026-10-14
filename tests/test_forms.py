import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from renmodpy import FormField, RecordDraft, RecordStore


class RecordFormTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.records = RecordStore(Path(self.directory.name) / "records.json")
        self.form = RecordDraft()

    def test_required_and_length_errors_keep_the_draft_without_writing(self):
        self.form.values["body"] = "A note"
        self.assertFalse(self.form.submit(self.records, 0))
        self.form.values["title"] = "x" * 81
        self.assertFalse(self.form.submit(self.records, 0))
        self.assertEqual(self.form.values["body"], "A note")
        self.assertEqual(self.records.list(), [])
        self.assertFalse(self.form.needs_reload)

    def test_edit_preserves_fields_outside_the_form_and_cancel_leaves_disk_intact(self):
        identifier = self.records.create({"title": "Original", "body": "Text", "extra": "Keep"})
        before = self.records.path.read_bytes()
        self.form.edit(self.records.snapshot(), identifier)
        self.form.values["title"] = "Cancelled"
        self.form.cancel()
        self.assertEqual(self.records.path.read_bytes(), before)
        self.form.edit(self.records.snapshot(), identifier)
        self.form.values["title"] = "Edited"
        self.assertTrue(self.form.submit(self.records, self.records.snapshot()["revision"]))
        self.assertEqual(self.records.list()[0]["values"],
                         {"title": "Edited", "body": "Text", "extra": "Keep"})

    def test_stale_edit_blocks_writes_until_explicit_reload_and_keeps_newer_rows(self):
        identifier = self.records.create({"title": "Original"})
        self.form.edit(self.records.snapshot(), identifier)
        self.form.values["title"] = "My draft"
        self.records.create({"title": "Newer"})
        self.assertFalse(self.form.submit(self.records, self.records.snapshot()["revision"]))
        self.assertTrue(self.form.needs_reload)
        self.assertEqual(self.form.values["title"], "My draft")
        self.assertFalse(self.form.submit(self.records, self.records.snapshot()["revision"]))
        self.form.reload(self.records.snapshot())
        self.assertTrue(self.form.submit(self.records, self.records.snapshot()["revision"]))
        self.assertEqual([r["values"]["title"] for r in self.records.list()], ["My draft", "Newer"])

    def test_reload_after_delete_keeps_draft_and_creates_a_new_identity(self):
        identifier = self.records.create({"title": "Original"})
        self.form.edit(self.records.snapshot(), identifier)
        self.form.values["title"] = "Keep this draft"
        self.records.delete(identifier)
        self.assertFalse(self.form.submit(self.records, self.records.snapshot()["revision"]))
        self.form.reload(self.records.snapshot())
        self.assertIsNone(self.form.editing_id)
        self.assertEqual(self.form.values["title"], "Keep this draft")
        self.assertTrue(self.form.submit(self.records, self.records.snapshot()["revision"]))
        self.assertNotEqual(self.records.list()[0]["id"], identifier)

    def test_failed_write_keeps_draft_until_reload_without_saving_a_duplicate(self):
        self.form.values["title"] = "Keep me"
        with patch("renmodpy.records.os.replace", side_effect=OSError("unavailable")):
            self.assertFalse(self.form.submit(self.records, 0))
        self.assertEqual(self.form.values["title"], "Keep me")
        self.assertTrue(self.form.needs_reload)
        self.assertEqual(self.records.list(), [])
        self.form.reload(self.records.snapshot())
        self.assertTrue(self.form.submit(self.records, 0))
        self.assertEqual(len(self.records.list()), 1)

    def test_custom_multiline_fields_and_pickled_draft_have_no_store_dependency(self):
        form = RecordDraft((FormField("name", "Name", required=True, max_length=80),
                            FormField("notes", "Notes", multiline=True)))
        form.values.update(name="  灯台  ", notes="First line\nSecond line")
        restored = pickle.loads(pickle.dumps(form))
        self.assertTrue(restored.submit(self.records, 0))
        self.assertEqual(self.records.list()[0]["values"],
                         {"name": "灯台", "notes": "First line\nSecond line"})
        values = form.values
        form.cancel()
        self.assertIs(form.values, values)

    def test_invalid_or_duplicate_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            FormField("bad", "Bad", max_length=True)
        with self.assertRaises(ValueError):
            RecordDraft((FormField("same", "One"), FormField("same", "Two")))
        with self.assertRaises(ValueError):
            RecordDraft(())

    def test_paste_appends_unicode_without_writing_or_clearing_stale_edit(self):
        identifier = self.records.create({"title": "Original", "body": "First ", "extra": "Keep"})
        before = self.records.path.read_bytes()
        self.form.edit(self.records.snapshot(), identifier)
        self.form.needs_reload = True
        values = self.form.values
        self.assertTrue(self.form.paste("body", "Blåbær\n{note} [value]"))
        self.assertIs(self.form.values, values)
        self.assertEqual(self.form.values["body"], "First Blåbær\n{note} [value]")
        self.assertTrue(self.form.needs_reload)
        self.assertEqual(self.form.editing_id, identifier)
        self.assertEqual(self.records.path.read_bytes(), before)
        self.assertEqual(pickle.loads(pickle.dumps(self.form)).values, self.form.values)

    def test_rejected_paste_preserves_all_fields(self):
        self.form.values.update(title="Keep title", body="Keep body")
        before = dict(self.form.values)
        for field, text in (("title", "line\nbreak"), ("title", "carriage\rreturn"),
                            ("title", "x" * 80), ("body", "x" * 1000),
                            ("body", ""), ("body", None), ("body", "bad\0text")):
            self.assertFalse(self.form.paste(field, text))
            self.assertEqual(self.form.values, before)
        self.assertEqual(self.records.list(), [])

    def test_paste_uses_custom_field_schema(self):
        form = RecordDraft((FormField("notes", "Field notes", multiline=True, max_length=20),))
        self.assertTrue(form.paste("notes", "灯台\nBlåbær"))
        self.assertEqual(form.values, {"notes": "灯台\nBlåbær"})
        with self.assertRaises(ValueError):
            form.paste("body", "Unknown")
