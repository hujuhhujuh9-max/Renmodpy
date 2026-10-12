"""Native IO through the donor's app class loader, with owner-thread results."""

import threading

from . import services
from .android_jni import app_loader_callback


def run(handler, callback, error_message):
    engine = services.owner()
    prepared = app_loader_callback(handler)

    def work():
        try:
            result, error = prepared(), None
        except Exception:
            result, error = None, error_message
        # Only plain values cross back to the engine; never a native exception.
        engine.invoke_in_main_thread(callback, result, error)

    threading.Thread(target=work, daemon=True, name="RenModPy native IO").start()
