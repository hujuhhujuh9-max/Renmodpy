import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

from renmodpy import services
from renmodpy.deep_links import package_scheme, parse_record_uri, record_uri


class RecordLinkTests(unittest.TestCase):
    identifier = "a1" * 16
    package = "org.example.story"

    def test_round_trip_uses_exact_saved_id_and_project_identity(self):
        uri = record_uri(self.package, self.identifier)
        self.assertEqual(uri, self.package + "://records/" + self.identifier)
        self.assertEqual(parse_record_uri(uri, self.package), self.identifier)
        self.assertIsNone(parse_record_uri(uri, "org.example.other"))
        self.assertEqual(package_scheme("org.example.my_story"), "org.example.my+story")
        self.assertEqual(parse_record_uri(record_uri("org.example.my_story", self.identifier),
                                         "org.example.my_story"), self.identifier)

    def test_links_cannot_select_labels_files_saves_collections_or_query_actions(self):
        uri = record_uri(self.package, self.identifier)
        for invalid in (None, b"not text", "https://example.org/records/" + self.identifier,
                        uri + "?action=delete", uri + "#load", uri + "/", uri + "\n", uri + "\0",
                        uri.replace("records/", "records/../"), uri.replace("records/", "start/"),
                        uri.replace("records/", "records/other/"), uri.replace("a1", "%611"),
                        uri.replace("records", "user@records"), uri.upper(), "x" * 257):
            with self.subTest(uri=invalid):
                self.assertIsNone(parse_record_uri(invalid, self.package))

    def test_link_builder_rejects_paths_and_invalid_project_identities(self):
        for identifier in ("../save", "", "a" * 31, "A" * 32, None):
            with self.assertRaises(ValueError):
                record_uri(self.package, identifier)
        for package in ("org.example/story", "", "http://example.org", "org.Example.story"):
            with self.assertRaises(ValueError):
                record_uri(package, self.identifier)


class AndroidLinkDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.engine = types.SimpleNamespace(android=True)
        self.delivered = []
        services.bind(self.engine, data_directory=self.directory.name,
                      deep_link_handler=lambda identifier: self.delivered.append((identifier, threading.get_ident())))
        self.activity = types.SimpleNamespace(mRenModPyDeepLinksEnabled=True,
            getPackageName=lambda: "org.example.story")
        self.pending = None
        def take():
            uri, self.pending = self.pending, None
            return uri
        self.activity.takeRenModPyDeepLink = take
        jnius = types.SimpleNamespace(autoclass=lambda name: types.SimpleNamespace(mActivity=self.activity))
        with patch.dict(sys.modules, {"jnius": jnius}):
            sys.modules.pop("renmodpy.android_deep_links", None)
            from renmodpy import android_deep_links
        # Explicitly rebind the cached JNI import: other suites use independent fixtures.
        binding = patch.object(android_deep_links, "autoclass", jnius.autoclass)
        binding.start()
        self.addCleanup(binding.stop)

    def test_each_delivery_is_consumed_once_on_owner_without_modifying_saved_data(self):
        identifier = services.records().create({"title": "Current Record"})
        before = services.records().snapshot()
        self.pending = services.record_link(identifier)
        services.poll_services()
        services.poll_services()
        self.assertEqual(self.delivered, [(identifier, threading.get_ident())])
        self.assertEqual(services.records().snapshot(), before)
        # A second native delivery of the same URI is a new explicit request.
        self.pending = services.record_link(identifier)
        services.poll_services()
        self.assertEqual(len(self.delivered), 2)

    def test_invalid_native_delivery_is_ignored_without_opening_a_screen(self):
        self.pending = "org.example.other://records/" + "a" * 32
        services.poll_services()
        self.assertEqual(self.delivered, [])
        self.assertIsNone(self.pending)

    def test_opt_in_and_host_availability(self):
        self.assertTrue(services.deep_links_enabled())
        self.activity.mRenModPyDeepLinksEnabled = False
        self.assertFalse(services.deep_links_enabled())
        with self.assertRaises(ValueError):
            services.record_link("a" * 32)
        services.bind(types.SimpleNamespace(android=False))
        self.assertFalse(services.deep_links_enabled())
        with self.assertRaises(ValueError):
            services.record_link("a" * 32)
        services.poll_services()

    def test_polling_on_worker_cannot_consume_an_intent(self):
        self.pending = "org.example.story://records/" + "a" * 32
        errors = []
        def worker():
            try:
                services.poll_services()
            except RuntimeError as error:
                errors.append(str(error))
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
        self.assertEqual(len(errors), 1)
        self.assertIsNotNone(self.pending)
        self.assertEqual(self.delivered, [])
