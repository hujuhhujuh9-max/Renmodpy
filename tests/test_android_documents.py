import importlib.util
from pathlib import Path
import types
import unittest
from unittest.mock import Mock, patch

from renmodpy import services


class AndroidDocumentTests(unittest.TestCase):
    def setUp(self):
        self.engine = types.SimpleNamespace(invoke_in_main_thread=Mock())
        services.bind(self.engine)
        self.activity = types.SimpleNamespace(mActivityResultRequestCode=-1, mActivityResultResultCode=0,
                                              mActivityResultResultData=None, startActivityForResult=Mock())
        self.ui, self.work = [], []
        class Intent:
            ACTION_OPEN_DOCUMENT, ACTION_CREATE_DOCUMENT = "open", "create"
            CATEGORY_OPENABLE, EXTRA_TITLE = "openable", "title"
            def __init__(self, action): self.action, self.extras = action, {}
            def addCategory(self, category): self.category = category
            def setType(self, mime): self.mime = mime
            def putExtra(self, key, value): self.extras[key] = value
        jnius = types.ModuleType("jnius")
        classes = {"android.content.Intent": Intent, "java.lang.String": str,
                   "org.renpy.android.PythonSDLActivity": types.SimpleNamespace(mActivity=self.activity)}
        jnius.autoclass = classes.__getitem__
        ui = types.ModuleType("renmodpy.android_jni")
        ui.run_on_ui_thread = lambda handler, on_error: self.ui.append((handler, on_error))
        worker = types.ModuleType("renmodpy.android_workers")
        worker.run = lambda handler, callback, error: self.work.append((handler, callback, error))
        path = Path(__file__).resolve().parents[1] / "engine/python/renmodpy/android_documents.py"
        spec = importlib.util.spec_from_file_location("renmodpy.android_documents", path)
        self.backend = importlib.util.module_from_spec(spec)
        with patch.dict("sys.modules", {"jnius": jnius, ui.__name__: ui, worker.__name__: worker}):
            spec.loader.exec_module(self.backend)

    def test_launch_is_deferred_and_cancel_returns_plain_values_once(self):
        done = Mock()
        self.backend.request("read", done, "application/json", limit=100)
        self.activity.startActivityForResult.assert_not_called()
        self.ui.pop()[0]()
        intent, request = self.activity.startActivityForResult.call_args.args
        self.assertEqual((intent.action, intent.category, intent.mime), ("open", "openable", "application/json"))
        self.activity.mActivityResultRequestCode = request
        # Native cancellation has no result Intent and must never dereference it.
        self.backend.poll(); self.backend.poll()
        done.assert_called_once_with(None, None)
        self.assertIsNone(self.backend._pending)
        self.assertEqual(self.work, [])

    def test_another_activity_result_cannot_complete_this_picker(self):
        done = Mock()
        self.backend.request("read", done, "text/plain", limit=100)
        self.activity.mActivityResultRequestCode = 19
        self.backend.poll()
        done.assert_not_called()
        with self.assertRaises(services.FileError):
            self.backend.request("read", done, "text/plain", limit=100)

    def test_io_is_deferred_until_selection_and_callback_clears_busy_before_reentry(self):
        done = Mock(side_effect=lambda value, error: self.backend.request("read", Mock(), "text/plain", limit=100))
        self.backend.request("write", done, "application/json", filename="notes.json", text="Blåbær")
        self.ui.pop()[0]()
        uri = types.SimpleNamespace(getScheme=lambda: "content", toString=lambda: "content://documents/note")
        self.activity.mActivityResultRequestCode = self.backend._pending["request"]
        self.activity.mActivityResultResultCode = -1
        self.activity.mActivityResultResultData = types.SimpleNamespace(getData=lambda: uri)
        self.backend.poll(); self.backend.poll()
        done.assert_not_called()
        self.assertEqual(len(self.work), 1)
        self.work.pop()[1](True, None)
        done.assert_called_once_with(True, None)
        self.assertEqual(self.backend._pending["operation"], "read")

    def test_ui_dispatch_error_is_queued_on_owner_and_releases_request(self):
        done = Mock()
        self.backend.request("read", done, "text/plain", limit=100)
        self.ui.pop()[1](RuntimeError("failed"))
        done.assert_not_called()
        callback, *args = self.engine.invoke_in_main_thread.call_args.args
        callback(*args)
        done.assert_called_once_with(None, "The Android file picker could not be opened.")
        self.assertIsNone(self.backend._pending)
