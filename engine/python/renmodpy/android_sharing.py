"""Android's text chooser, dispatched through the existing app JNI callback."""

from jnius import autoclass, cast

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
