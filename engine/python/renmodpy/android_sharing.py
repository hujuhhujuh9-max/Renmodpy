"""Android's text chooser, dispatched through the existing app JNI callback."""

from jnius import autoclass, cast

from .android_jni import run_on_ui_thread


def _launch(activity, chooser):
    """Only called on Android's UI thread."""
    activity.startActivity(chooser)


def share_text(text, subject, on_error):
    Intent = autoclass("android.content.Intent")
    activity = autoclass("org.renpy.android.PythonSDLActivity").mActivity
    intent = Intent(Intent.ACTION_SEND)
    intent.setType("text/plain")
    intent.putExtra(Intent.EXTRA_TEXT, text)
    if subject:
        intent.putExtra(Intent.EXTRA_SUBJECT, subject)
    # This JNI overload requires a Java CharSequence, not a Python string.
    title = cast("java.lang.CharSequence", autoclass("java.lang.String")("Share text"))
    chooser = Intent.createChooser(intent, title)
    run_on_ui_thread(lambda: _launch(activity, chooser), on_error=on_error)
