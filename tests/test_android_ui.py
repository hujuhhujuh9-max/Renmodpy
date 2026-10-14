import gc
import importlib.util
from pathlib import Path
import threading
import types
import unittest
import weakref
from unittest.mock import Mock, patch


class AndroidUiTests(unittest.TestCase):
    def setUp(self):
        local = threading.local()
        class JavaThread:
            def __init__(self):
                self.loader = "original-loader"
            def getContextClassLoader(self):
                return self.loader
            def setContextClassLoader(self, loader):
                self.loader = loader
            @staticmethod
            def currentThread():
                if not hasattr(local, "thread"):
                    local.thread = JavaThread()
                return local.thread

        class JavaClass:
            def __new__(cls, *args, **kwargs):
                # Pyjnius's Cython __cinit__(*args) receives constructor
                # arguments before the Python subclass __init__ can bind them.
                if kwargs:
                    raise TypeError("Native __cinit__ does not accept keyword arguments")
                return super().__new__(cls)
            def __init__(self):
                self.j_self = self

        class Runnable:
            # Like JNI's native callback handle, this does not keep its
            # Python target alive. The dispatcher must retain the target.
            def __init__(self, target):
                self.target = weakref.ref(target)
            def run(self):
                target = self.target()
                if target is None:
                    raise RuntimeError("Callback was released before dispatch")
                target.run()

        self.thread = JavaThread
        self.queue = []
        self.activity = types.SimpleNamespace(
            getClassLoader=lambda: "app-loader", runOnUiThread=Mock(side_effect=self.queue.append))
        classes = {"java.lang.Thread": JavaThread,
                   "org.renpy.android.PythonSDLActivity": types.SimpleNamespace(mActivity=self.activity)}
        jnius = types.ModuleType("jnius")
        jnius.PythonJavaClass = JavaClass
        jnius.autoclass = classes.__getitem__
        jnius.cast = lambda name, target: Runnable(target)
        jnius.java_method = lambda signature: lambda method: method
        with patch.dict("sys.modules", {"jnius": jnius}):
            path = Path(__file__).resolve().parents[1] / "engine/python/renmodpy/android_jni.py"
            spec = importlib.util.spec_from_file_location("renmodpy.android_jni", path)
            self.helper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.helper)

    def dispatch(self):
        restored = []
        runnable = self.queue.pop(0)
        def ui():
            runnable.run()
            restored.append(self.thread.currentThread().getContextClassLoader())
        thread = threading.Thread(target=ui, name="test-android-ui")
        thread.start()
        thread.join()
        self.assertEqual(restored, ["original-loader"])

    def test_queued_ui_callback_is_retained_and_app_loader_is_restored(self):
        calls = []
        caller = threading.get_ident()
        self.helper.run_on_ui_thread(lambda: calls.append(
            (threading.get_ident(), self.thread.currentThread().getContextClassLoader())))
        self.assertEqual(calls, [])
        self.assertEqual(len(self.helper._ui_calls), 1)
        gc.collect()
        self.dispatch()
        self.assertNotEqual(calls[0][0], caller)
        self.assertEqual(calls[0][1], "app-loader")
        self.assertEqual(len(self.helper._ui_calls), 0)
        self.assertEqual(self.thread.currentThread().getContextClassLoader(), "original-loader")

    def test_ui_error_reports_once_and_releases_the_native_callback(self):
        error = RuntimeError("Activity refused the intent")
        reported = []
        def fail():
            raise error
        self.helper.run_on_ui_thread(fail, on_error=reported.append)
        self.dispatch()
        self.assertEqual(reported, [error])
        self.assertEqual(len(self.helper._ui_calls), 0)

    def test_scheduling_failure_releases_the_undispatched_callback(self):
        self.activity.runOnUiThread.side_effect = RuntimeError("Activity unavailable")
        with self.assertRaisesRegex(RuntimeError, "Activity unavailable"):
            self.helper.run_on_ui_thread(lambda: None)
        self.assertEqual(len(self.helper._ui_calls), 0)
        self.assertEqual(self.queue, [])

    def test_existing_worker_callback_still_returns_and_raises_with_app_loader(self):
        execute = self.helper.app_loader_callback(lambda: self.thread.currentThread().getContextClassLoader())
        self.assertEqual(execute(), "app-loader")
        self.assertEqual(self.thread.currentThread().getContextClassLoader(), "original-loader")
        def fail():
            raise ValueError("Worker failed")
        with self.assertRaisesRegex(ValueError, "Worker failed"):
            self.helper.app_loader_callback(fail)()
        self.assertEqual(self.thread.currentThread().getContextClassLoader(), "original-loader")
