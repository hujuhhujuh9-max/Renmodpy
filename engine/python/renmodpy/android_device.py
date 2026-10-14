"""Native private storage and touch feedback behind the owning Python API."""

from jnius import autoclass

from . import services
from .android_jni import run_on_ui_thread
from .android_workers import run as run_worker


def _perform_haptic(activity, code):
    return bool(activity.getWindow().getDecorView().performHapticFeedback(code))


def secure(operation, key, value, callback):
    services.owner()
    if autoclass("android.os.Build$VERSION").SDK_INT < 23:
        raise services.StorageError("Private storage requires Android 6 or later.")
    activity = autoclass("org.renpy.android.PythonSDLActivity").mActivity
    def work():
        storage = autoclass("org.renpy.android.RenModPySecureStorage")
        JavaString = autoclass("java.lang.String")
        if operation == "get":
            result = storage.get(activity, JavaString(key))
            return None if result is None else str(result)
        if operation == "set":
            return bool(storage.set(activity, JavaString(key), JavaString(value)))
        return bool(storage.delete(activity, JavaString(key)))
    run_worker(work, callback, "Private storage could not be accessed. Existing data was preserved.")


def haptic(kind, callback):
    engine = services.owner()
    activity = autoclass("org.renpy.android.PythonSDLActivity").mActivity
    constants = autoclass("android.view.HapticFeedbackConstants")
    code = constants.CLOCK_TICK if kind == "selection" else constants.LONG_PRESS
    def perform():
        accepted = _perform_haptic(activity, code)
        if callback is not None:
            engine.invoke_in_main_thread(callback, accepted, None)
    def failed(error):
        if callback is not None:
            engine.invoke_in_main_thread(callback, None, "Touch feedback is unavailable.")
    run_on_ui_thread(perform, on_error=failed)
