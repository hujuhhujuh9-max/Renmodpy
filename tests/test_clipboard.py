import threading
import types
import unittest
from unittest.mock import Mock, patch

from renmodpy import services


class ClipboardTests(unittest.TestCase):
    def setUp(self):
        services.bind(types.SimpleNamespace(android=False))
        self.pygame = types.ModuleType("pygame")
        self.pygame.SCRAP_TEXT = "text"
        self.pygame.scrap = Mock()
        self.modules = patch.dict("sys.modules", {"pygame": self.pygame, "pygame.scrap": self.pygame.scrap})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def test_unicode_multiline_and_literal_markup_use_utf8(self):
        text = "Blåbær, café, Ω\nLiteral {note} [value]"
        services.copy_text(text)
        self.pygame.scrap.put.assert_called_once_with("text", text.encode("utf-8"))
        self.pygame.scrap.get.return_value = text.encode("utf-8") + b"\0"
        self.assertEqual(services.clipboard_text(), text)

    def test_empty_or_non_text_clipboard_is_empty(self):
        for value in (None, b""):
            self.pygame.scrap.get.return_value = value
            self.assertEqual(services.clipboard_text(), "")

    def test_unavailable_clipboard_and_invalid_utf8_are_reported(self):
        self.pygame.scrap.put.side_effect = RuntimeError("backend unavailable")
        with self.assertRaises(services.ClipboardError):
            services.copy_text("Keep draft")
        self.pygame.scrap.get.side_effect = RuntimeError("backend unavailable")
        with self.assertRaises(services.ClipboardError):
            services.clipboard_text()
        self.pygame.scrap.get.side_effect = None
        self.pygame.scrap.get.return_value = b"\xff"
        with self.assertRaises(services.ClipboardError):
            services.clipboard_text()

    def test_invalid_copy_does_not_change_clipboard(self):
        for value in (None, 7, "contains\0null"):
            with self.assertRaises(ValueError):
                services.copy_text(value)
        self.pygame.scrap.put.assert_not_called()

    def test_worker_cannot_access_clipboard(self):
        errors = []

        def worker():
            for operation in (lambda: services.copy_text("worker"), services.clipboard_text):
                try:
                    operation()
                except RuntimeError as error:
                    errors.append(error)

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
        self.assertEqual(len(errors), 2)
        self.pygame.scrap.put.assert_not_called()
        self.pygame.scrap.get.assert_not_called()
