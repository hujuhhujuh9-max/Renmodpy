import importlib.util
from pathlib import Path
import types
import unittest
from unittest.mock import Mock, patch


class AndroidSharingContractTests(unittest.TestCase):
    def test_chooser_uses_java_char_sequence_and_defers_activity_launch(self):
        class JavaString:
            def __init__(self, value):
                self.value = value

        class CharSequence:
            def __init__(self, value):
                self.value = value

        class Intent:
            ACTION_SEND = "send"
            EXTRA_TEXT = "text"
            EXTRA_SUBJECT = "subject"
            def __init__(self, action):
                self.action, self.extras = action, {}
            def setType(self, mime):
                self.mime = mime
            def putExtra(self, key, value):
                # The locked JNI binding chooses char[] for Python str
                # values; Java String extras require explicit Java objects.
                self.extras[key] = value.value if isinstance(value, JavaString) else list(value)
            @staticmethod
            def createChooser(intent, title):
                # The real JNI signature accepts CharSequence, and does not
                # convert Python str for this overload (Android regression).
                if not isinstance(title, CharSequence):
                    raise TypeError("createChooser requires a Java CharSequence")
                return types.SimpleNamespace(intent=intent, title=title.value)

        queued = []
        activity = types.SimpleNamespace(startActivity=Mock())
        classes = {"android.content.Intent": Intent, "java.lang.String": JavaString,
                   "org.renpy.android.PythonSDLActivity": types.SimpleNamespace(mActivity=activity)}
        jnius = types.ModuleType("jnius")
        jnius.autoclass = classes.__getitem__
        def cast(name, value):
            self.assertEqual(name, "java.lang.CharSequence")
            self.assertIsInstance(value, JavaString)
            return CharSequence(value.value)
        jnius.cast = cast
        ui = types.ModuleType("renmodpy.android_jni")
        ui.run_on_ui_thread = lambda handler, on_error: queued.append((handler, on_error))
        path = Path(__file__).resolve().parents[1] / "engine/python/renmodpy/android_sharing.py"
        spec = importlib.util.spec_from_file_location("renmodpy.android_sharing", path)
        backend = importlib.util.module_from_spec(spec)
        with patch.dict("sys.modules", {"jnius": jnius, ui.__name__: ui}):
            spec.loader.exec_module(backend)
            error = Mock()
            text = "Blåbær\nLiteral {note} [value]"
            backend.share_text(text, "Field notes", error)
            activity.startActivity.assert_not_called()
            handler, callback = queued.pop()
            self.assertIs(callback, error)
            handler()
            chooser = activity.startActivity.call_args.args[0]
            self.assertEqual(chooser.title, "Share text")
            self.assertEqual(chooser.intent.mime, "text/plain")
            self.assertEqual(chooser.intent.extras, {"text": text, "subject": "Field notes"})
