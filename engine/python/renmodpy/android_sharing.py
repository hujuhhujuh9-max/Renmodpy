"""Android's text chooser, dispatched through the existing app JNI callback."""

from jnius import autoclass, cast
from pathlib import Path
import shutil
import time
import uuid

from .android_jni import run_on_ui_thread


def _launch(activity, chooser):
    """Only called on Android's UI thread."""
    activity.startActivity(chooser)


def share_text(text, subject, on_error):
    Intent = autoclass("android.content.Intent")
    JavaString = autoclass("java.lang.String")
    activity = autoclass("org.renpy.android.PythonSDLActivity").mActivity
    intent = Intent(Intent.ACTION_SEND)
    intent.setType("text/plain")
    # Python str can match putExtra's char[] overload in this JNI binding.
    intent.putExtra(Intent.EXTRA_TEXT, JavaString(text))
    if subject:
        intent.putExtra(Intent.EXTRA_SUBJECT, JavaString(subject))
    # This JNI overload requires a Java CharSequence, not a Python string.
    title = cast("java.lang.CharSequence", JavaString("Share text"))
    chooser = Intent.createChooser(intent, title)
    run_on_ui_thread(lambda: _launch(activity, chooser), on_error=on_error)


def share_file(filename, data, mime, subject, on_error):
    Intent = autoclass("android.content.Intent")
    JavaString = autoclass("java.lang.String")
    activity = autoclass("org.renpy.android.PythonSDLActivity").mActivity
    root = Path(str(activity.getCacheDir().getAbsolutePath())) / "renmodpy-share"
    root.mkdir(parents=True, exist_ok=True)
    # A recipient needs the file after the launcher returns. Keep recent
    # exports, and discard old cache directories on the next explicit share.
    for directory in root.iterdir():
        if directory.is_dir() and directory.stat().st_mtime < time.time() - 86400:
            shutil.rmtree(directory)
    directory = root / uuid.uuid4().hex
    directory.mkdir()
    path = directory / filename
    path.write_bytes(data)
    uri = autoclass("org.renpy.android.RenPyFileProvider").getUriForFile(
        activity, activity.getPackageName() + ".fileprovider", autoclass("java.io.File")(str(path)))
    intent = Intent(Intent.ACTION_SEND)
    intent.setType(mime)
    intent.putExtra(Intent.EXTRA_STREAM, cast("android.os.Parcelable", uri))
    title = cast("java.lang.CharSequence", JavaString(filename))
    intent.setClipData(autoclass("android.content.ClipData").newRawUri(title, uri))
    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    if subject:
        intent.putExtra(Intent.EXTRA_SUBJECT, JavaString(subject))
    chooser = Intent.createChooser(intent, cast("java.lang.CharSequence", JavaString("Share file")))
    chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    run_on_ui_thread(lambda: _launch(activity, chooser), on_error=on_error)
