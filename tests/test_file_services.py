import threading
import types
import unittest
from unittest.mock import Mock, patch

import renmodpy
from renmodpy import services


class FileServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = types.SimpleNamespace(android=True, notify=Mock(), invoke_in_main_thread=Mock())
        services.bind(self.engine)
        self.documents = types.ModuleType("renmodpy.android_documents")
        self.documents.request = Mock()
        self.documents._pending = None
        self.sharing = types.ModuleType("renmodpy.android_sharing")
        self.sharing.share_file = Mock()
        for name, module in (("android_documents", self.documents), ("android_sharing", self.sharing)):
            p = patch.object(renmodpy, name, module, create=True)
            p.start(); self.addCleanup(p.stop)

    def test_pick_and_export_preserve_callback_and_utf8_payload(self):
        done = Mock()
        services.pick_text(done, mime="application/json", max_bytes=100)
        self.documents.request.assert_called_with("read", done, "application/json", limit=100)
        text = "Café Ω 🌊\nLiteral {note} [value]"
        services.export_text("notes.json", text, done, mime="application/json")
        self.documents.request.assert_called_with("write", done, "application/json", filename="notes.json", text=text)
        done.assert_not_called()

    def test_invalid_names_sizes_callbacks_and_mime_never_open_android(self):
        for name in ("", ".", "..", "../note", "a/b", "a\\b", "bad\nname"):
            with self.assertRaises(ValueError):
                services.export_text(name, "text", Mock())
        for size in (0, True, 8 * 1024 * 1024 + 1):
            with self.assertRaises(ValueError):
                services.pick_text(Mock(), max_bytes=size)
        for mime in ("json", "application/json\n", None):
            with self.assertRaises(ValueError):
                services.pick_text(Mock(), mime=mime)
        with self.assertRaises(ValueError):
            services.pick_text(None)
        self.documents.request.assert_not_called()

    def test_busy_picker_error_is_preserved_and_launch_failures_are_friendly(self):
        self.documents.request.side_effect = services.FileError("Finish the current request")
        with self.assertRaisesRegex(services.FileError, "Finish"):
            services.pick_text(Mock())
        self.documents.request.side_effect = RuntimeError("native failure")
        with self.assertRaisesRegex(services.FileError, "could not be opened"):
            services.pick_text(Mock())

    def test_file_sharing_requires_bytes_and_queues_ui_errors(self):
        data = b"{\"version\":1}"
        services.share_file("backup.json", data, mime="application/json")
        args, kwargs = self.sharing.share_file.call_args
        self.assertEqual(args, ("backup.json", data, "application/json", ""))
        kwargs["on_error"](RuntimeError("failed"))
        self.engine.notify.assert_not_called()
        self.engine.invoke_in_main_thread.assert_called_once()
        for payload in ("text", b"", bytearray(b"data")):
            with self.assertRaises(ValueError):
                services.share_file("notes.json", payload)

    def test_host_and_worker_cannot_request_platform_files(self):
        self.engine.android = False
        for request in (lambda: services.pick_text(Mock()), lambda: services.export_text("note", "text", Mock()),
                        lambda: services.share_file("note", b"text")):
            with self.assertRaises((services.FileError, services.ShareError)):
                request()
        errors = []
        def worker():
            try: services.pick_text(Mock())
            except RuntimeError as error: errors.append(error)
        thread = threading.Thread(target=worker);thread.start();thread.join()
        self.assertEqual(len(errors), 1)
        self.documents.request.assert_not_called()
