"""Enter APK Java callbacks without changing Ren'Py's interpreter ownership.

JNI FindClass on a Python-created thread otherwise uses Android's system loader.
The packaged NativeInvocationHandler supplies the app loader during its callback.
Use call_with_app_class_loader for Android JNI work on additional Python threads.
"""

from jnius import PythonJavaClass, autoclass, cast, java_method

_Thread = autoclass("java.lang.Thread")
_app_loader = autoclass("org.renpy.android.PythonSDLActivity").mActivity.getClassLoader()
_ui_calls = set()


class _JavaCall(PythonJavaClass):
    __javainterfaces__ = ["java/lang/Runnable"]
    # Runnable is a system interface; the native callback belongs to the APK.
    __javacontext__ = "system"

    def __init__(self, handler, on_finish=None):
        self.handler = handler
        self.on_finish = on_finish
        self.result = None
        self.error = None
        self.called = False
        super().__init__()
        # Pyjnius wraps Android's generated proxy as java.lang.Object.
        self.runnable = cast("java.lang.Runnable", self.j_self)

    @java_method("()V")
    def run(self):
        thread = _Thread.currentThread()
        original = thread.getContextClassLoader()
        self.called = True
        try:
            thread.setContextClassLoader(_app_loader)
            self.result = self.handler()
        except BaseException as error:
            self.error = error
        finally:
            thread.setContextClassLoader(original)
            if self.on_finish is not None:
                self.on_finish(self)

    def execute(self):
        self.runnable.run()
        if not self.called:
            raise RuntimeError("Android did not dispatch the Python JNI callback")
        if self.error is not None:
            raise self.error
        return self.result


def app_loader_callback(handler):
    """Prepare on the Android owner thread; retain the proxy until it returns."""
    return _JavaCall(handler).execute


def call_with_app_class_loader(handler, *args, **kwargs):
    """Run JNI work from a Python worker after the owner prepared its callback."""
    return app_loader_callback(lambda: handler(*args, **kwargs))()


def run_on_ui_thread(handler, *, on_error=None):
    """Queue a retained JNI callback on Android's UI thread without blocking SDL.

    Prepare this callback on the Android owner thread.
    on_error runs on that UI thread; use Ren'Py's invoke_in_main_thread to
    deliver any engine notification. The native proxy stays alive until run ends.
    """
    def finished(call):
        try:
            if call.error is not None and on_error is not None:
                on_error(call.error)
        finally:
            _ui_calls.discard(call)

    call = _JavaCall(handler, on_finish=finished)
    _ui_calls.add(call)
    try:
        activity = autoclass("org.renpy.android.PythonSDLActivity").mActivity
        activity.runOnUiThread(call.runnable)
    except Exception:
        _ui_calls.discard(call)
        raise

