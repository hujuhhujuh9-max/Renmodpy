import types
import unittest
from unittest.mock import Mock, patch

import renmodpy
from renmodpy import services


class DeviceServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = types.SimpleNamespace(android=True)
        services.bind(self.engine)
        self.backend = types.ModuleType("renmodpy.android_device")
        self.backend.secure, self.backend.haptic = Mock(), Mock()
        p = patch.object(renmodpy, "android_device", self.backend, create=True)
        p.start(); self.addCleanup(p.stop)

    def test_private_values_go_only_to_the_native_backend(self):
        done = Mock()
        services.secure_set("app.note", "Café Ω", done)
        self.backend.secure.assert_called_with("set", "app.note", "Café Ω", done)
        services.secure_get("app.note", done)
        self.backend.secure.assert_called_with("get", "app.note", "", done)
        services.secure_delete("app.note", done)
        self.backend.secure.assert_called_with("delete", "app.note", "", done)
        done.assert_not_called()

    def test_invalid_storage_values_and_host_are_rejected(self):
        for key in ("", " ", "bad\0key", "bad\nkey", 1):
            with self.assertRaises(ValueError): services.secure_get(key, Mock())
        with self.assertRaises(ValueError): services.secure_set("key", "é" * 40000, Mock())
        self.engine.android = False
        with self.assertRaises(services.StorageError): services.secure_get("key", Mock())
        self.backend.secure.assert_not_called()

    def test_feedback_validates_kind_without_claiming_physical_vibration(self):
        done = Mock()
        self.assertIsNone(services.haptic("confirm", done))
        self.backend.haptic.assert_called_once_with("confirm", done)
        done.assert_not_called()
        with self.assertRaises(ValueError): services.haptic("unsupported")
