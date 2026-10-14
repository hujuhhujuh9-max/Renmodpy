"""Drain native Intent delivery on Ren'Py's owner, outside story snapshots."""

from jnius import autoclass

from . import services
from .deep_links import parse_record_uri, record_uri


def _activity():
    services.owner()
    return autoclass("org.renpy.android.PythonSDLActivity").mActivity


def enabled():
    return bool(_activity().mRenModPyDeepLinksEnabled)


def link(identifier):
    activity = _activity()
    if not activity.mRenModPyDeepLinksEnabled:
        raise ValueError("Enable renmodpy_deep_links in the project's Android configuration.")
    return record_uri(str(activity.getPackageName()), identifier)


def poll():
    activity = _activity()
    uri = activity.takeRenModPyDeepLink()
    return parse_record_uri(str(uri), str(activity.getPackageName())) if uri is not None else None
