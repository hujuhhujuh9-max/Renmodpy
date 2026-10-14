"""One scoped Android picker at a time; native results never enter story saves."""

from jnius import autoclass

from . import services
from .android_jni import run_on_ui_thread
from .android_workers import run as run_worker

_pending = None
_request = 51000


def _finish(pending, value, error):
    global _pending
    services.owner()
    if _pending is not pending:
        return
    _pending = None
    pending["callback"](value, error)


def request(operation, callback, mime, filename="", text="", limit=0):
    global _pending, _request
    engine = services.owner()
    if _pending is not None:
        raise services.FileError("Finish the current file request first.")
    _request = 51000 + (_request - 51000 + 1) % 1000
    pending = {"request": _request, "operation": operation, "callback": callback,
               "text": text, "limit": limit, "phase": "waiting"}
    _pending = pending
    try:
        Intent = autoclass("android.content.Intent")
        JavaString = autoclass("java.lang.String")
        activity = autoclass("org.renpy.android.PythonSDLActivity").mActivity
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT if operation == "read" else Intent.ACTION_CREATE_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType(mime)
        if filename:
            intent.putExtra(Intent.EXTRA_TITLE, JavaString(filename))
        def launch():
            activity.mActivityResultRequestCode = -1
            activity.startActivityForResult(intent, pending["request"])
        run_on_ui_thread(launch, on_error=lambda error: engine.invoke_in_main_thread(
            _finish, pending, None, "The Android file picker could not be opened."))
    except Exception:
        _pending = None
        raise


def poll():
    services.owner()
    pending = _pending
    if pending is None or pending["phase"] != "waiting":
        return
    activity = autoclass("org.renpy.android.PythonSDLActivity").mActivity
    if activity.mActivityResultRequestCode != pending["request"]:
        return
    code, data = activity.mActivityResultResultCode, activity.mActivityResultResultData
    activity.mActivityResultRequestCode = -1
    activity.mActivityResultResultData = None
    if code != -1 or data is None:
        _finish(pending, None, None)
        return
    try:
        uri = data.getData()
        if uri is None or str(uri.getScheme()) != "content":
            raise ValueError("The selected document has no scoped URI.")
        location = str(uri.toString())
        pending["phase"] = "working"
        def io():
            # First app-class lookup occurs on the class-loader-bound worker.
            documents = autoclass("org.renpy.android.RenModPyDocuments")
            JavaString = autoclass("java.lang.String")
            if pending["operation"] == "read":
                return str(documents.readText(activity, JavaString(location), pending["limit"]))
            return bool(documents.writeText(activity, JavaString(location), JavaString(pending["text"])))
        run_worker(io, lambda result, error: _finish(pending, result, error),
                   "The document could not be read as UTF-8 within the size limit." if pending["operation"] == "read"
                   else "The document could not be written. Check the selected destination.")
    except Exception:
        _finish(pending, None, "The selected document could not be opened.")
