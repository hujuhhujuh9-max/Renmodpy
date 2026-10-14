import threading
import tempfile
import types
import unittest

from renmodpy import services


class NativeEngine:
    android = False

    def __init__(self):
        self.saves = {}
        self.store = types.SimpleNamespace(persistent=types.SimpleNamespace())
        self.calls = []

    def list_slots(self, pattern):
        return list(self.saves)

    def slot_json(self, slot):
        return self.saves.get(slot)

    def slot_mtime(self, slot):
        return 1

    def take_screenshot(self):
        pass

    def can_load(self, slot):
        return slot in self.saves

    def newest_slot(self, pattern):
        import re
        return next((slot for slot in reversed(self.saves) if re.fullmatch(pattern, slot)), None)

    def save_persistent(self):
        pass

    def save(self, slot, extra_info="", extra_json=None):
        self.saves[slot] = {"_save_name": extra_info, **(extra_json or {})}

    def unlink_save(self, slot):
        self.saves.pop(slot, None)

    def load(self, slot):
        self.calls.append(slot)


class NativeSaveTests(unittest.TestCase):
    def setUp(self):
        self.engine = NativeEngine()
        services.bind(self.engine)

    def test_stale_fingerprint_does_not_overwrite_or_delete_newer_save(self):
        slot = services.create_save("First", "Lighthouse")
        first = services.save_catalog()[0]
        services.overwrite_save(slot, first["fingerprint"], "Second", "Balcony")
        for action in (
            lambda: services.delete_save(slot, first["fingerprint"]),
            lambda: services.overwrite_save(slot, first["fingerprint"], "Stale"),
            lambda: services.load_save(slot, first["fingerprint"]),
        ):
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(self.engine.saves[slot]["_save_name"], "Second")

    def test_manual_browser_protects_resume_and_autosave_slots(self):
        self.engine.saves["renmodpy-resume"] = {"_save_name": "Resume"}
        self.engine.saves["_reload-1"] = {"_save_name": "Recovery"}
        services.save_quick()
        slot = services.create_save("Named")
        self.assertEqual([r["slot"] for r in services.save_catalog()], [slot])
        with self.assertRaises(ValueError):
            services.delete_save("renmodpy-resume", "anything")
        self.assertIn("renmodpy-resume", self.engine.saves)

    def test_replay_and_completion_keep_quick_and_named_saves_separate_from_resume(self):
        slot = services.create_save("Named")
        services.save_quick()
        services.save_resume()
        self.assertTrue(services.quick_available())
        self.engine.save("_reload-1")
        self.assertEqual(services.resume_slot(), "_reload-1")
        services.load_quick()
        self.assertEqual(self.engine.calls, [services.QUICK_SLOT])
        services.begin_story()
        self.assertIsNone(services.resume_slot())
        self.assertNotIn("_reload-1", self.engine.saves)
        services.save_resume()
        self.engine.save("_reload-1")
        services.finish_story("Finished")
        self.assertIsNone(services.resume_slot())
        self.assertNotIn("_reload-1", self.engine.saves)
        self.assertTrue(services.quick_available())
        self.assertIn(slot, self.engine.saves)

    def test_empty_quick_load_does_not_call_the_engine(self):
        with self.assertRaises(ValueError):
            services.load_quick()
        self.assertEqual(self.engine.calls, [])

    def test_named_record_collections_are_isolated_and_cannot_choose_a_path(self):
        with tempfile.TemporaryDirectory() as directory:
            services.bind(self.engine, data_directory=directory)
            first = services.records("field-notes")
            second = services.records()
            first.create({"title": "Only field notes"})
            self.assertIs(first, services.records("field-notes"))
            self.assertEqual(second.list(), [])
            for name in ("../escape", "", "a/b", "x" * 49):
                with self.assertRaises(ValueError):
                    services.records(name)

    def test_save_name_is_a_label_and_cannot_choose_a_path(self):
        slot = services.create_save("../../same label")
        self.assertRegex(slot, "^renmodpy-manual-[0-9a-f]{32}$")
        self.assertEqual(self.engine.saves[slot]["_save_name"], "../../same label")

    def test_worker_thread_cannot_call_native_save(self):
        errors = []
        def worker():
            try:
                services.create_save("Worker")
            except RuntimeError as error:
                errors.append(str(error))
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
        self.assertEqual(len(errors), 1)
        self.assertEqual(self.engine.saves, {})
