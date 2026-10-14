import threading
import types
import unittest
from unittest.mock import Mock, patch

import renmodpy
from renmodpy import services


class SharingTests(unittest.TestCase):
    def setUp(self):
        self.engine = types.SimpleNamespace(android=True, notify=Mock(), invoke_in_main_thread=Mock())
        services.bind(self.engine)
        self.backend = types.ModuleType("renmodpy.android_sharing")
        self.backend.share_text = Mock()
        self.modules = patch.dict("sys.modules", {self.backend.__name__: self.backend})
        self.attribute = patch.object(renmodpy, "android_sharing", self.backend, create=True)
        self.modules.start()
        self.attribute.start()
        self.addCleanup(self.modules.stop)
        self.addCleanup(self.attribute.stop)

    def test_unicode_multiline_and_literal_text_are_queued_without_a_send_result(self):
        text = "Blåbær, café, Ω\nLiteral {note} [value]"
        self.assertIsNone(services.share_text(text, subject="A {literal} [subject]"))
        args, kwargs = self.backend.share_text.call_args
        self.assertEqual(args, (text, "A {literal} [subject]"))
        self.assertTrue(callable(kwargs["on_error"]))
        self.engine.notify.assert_not_called()

    def test_invalid_text_and_subject_never_reach_android(self):
        for text in (None, 7, "", " \n\t", "bad\0text"):
            with self.assertRaises(ValueError):
                services.share_text(text)
        for subject in (None, 7, "bad\0subject"):
            with self.assertRaises(ValueError):
                services.share_text("Keep text", subject=subject)
        self.backend.share_text.assert_not_called()

    def test_host_does_not_claim_android_sharing(self):
        self.engine.android = False
        with self.assertRaisesRegex(services.ShareError, "available on Android"):
            services.share_text("Keep text")
        self.backend.share_text.assert_not_called()

    def test_dispatch_failure_becomes_a_friendly_service_error(self):
        self.backend.share_text.side_effect = RuntimeError("Activity unavailable")
        with self.assertRaisesRegex(services.ShareError, "could not be opened"):
            services.share_text("Keep text")
        self.engine.notify.assert_not_called()

    def test_ui_failure_queues_notification_instead_of_calling_engine_on_ui_thread(self):
        services.share_text("Keep text")
        report_error = self.backend.share_text.call_args.kwargs["on_error"]
        worker = threading.Thread(target=lambda: report_error(RuntimeError("No share target")))
        worker.start()
        worker.join()
        self.engine.notify.assert_not_called()
        self.engine.invoke_in_main_thread.assert_called_once_with(
            self.engine.notify, "Android sharing could not be opened.")

    def test_worker_cannot_request_platform_sharing(self):
        errors = []
        def worker():
            try:
                services.share_text("worker")
            except RuntimeError as error:
                errors.append(error)
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
        self.assertEqual(len(errors), 1)
        self.backend.share_text.assert_not_called()
