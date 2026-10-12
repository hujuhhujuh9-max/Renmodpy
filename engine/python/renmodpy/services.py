"""Native services owned by the Ren'Py thread, outside story snapshots."""

import hashlib
import json
import os
import re
import sys
import threading
import uuid
from pathlib import Path

from .records import RecordStore
from .transfers import MAX_DOCUMENT_BYTES


RESUME_SLOT = "renmodpy-resume"
QUICK_SLOT = "renmodpy-quick"
MANUAL_PATTERN = r"renmodpy-manual-[0-9a-f]{32}"
_engine = None
_thread = None
_records = {}
_data_directory = None


class ClipboardError(RuntimeError):
    """The platform clipboard could not provide or accept text."""


class ShareError(RuntimeError):
    """The Android text chooser could not be requested."""


class FileError(RuntimeError):
    """A scoped Android file operation could not be requested."""


class StorageError(RuntimeError):
    """Android private encrypted storage could not be requested."""


def _secure(operation, key, callback, value=""):
    engine = owner()
    if (not isinstance(key, str) or not 1 <= len(key) <= 128 or not key.strip()
            or not key.isprintable() or not callable(callback)):
        raise ValueError("Use a callback and a printable private-storage key of 1–128 characters.")
    if not isinstance(value, str) or len(value.encode("utf-8")) > 65536:
        raise ValueError("Use private text no larger than 64 KiB.")
    if not engine.android:
        raise StorageError("Private encrypted storage is available on Android.")
    try:
        from . import android_device
        android_device.secure(operation, key, value, callback)
    except StorageError:
        raise
    except Exception as error:
        raise StorageError("Private storage could not be requested.") from error


def secure_set(key, value, callback):
    """Store text with Android Keystore; callback(True, None) means committed."""
    _secure("set", key, callback, value)


def secure_get(key, callback):
    """Read private text; callback(None, None) means absent. Never log secrets."""
    _secure("get", key, callback)


def secure_delete(key, callback):
    """Delete private text; the result reports whether an entry existed."""
    _secure("delete", key, callback)


def haptic(kind="selection", callback=None):
    """Request native touch feedback; accepted does not prove physical vibration."""
    engine = owner()
    if kind not in ("selection", "confirm") or (callback is not None and not callable(callback)):
        raise ValueError("Choose selection or confirm feedback and an optional callback.")
    if not engine.android:
        raise RuntimeError("Touch feedback is available on Android.")
    from . import android_device
    android_device.haptic(kind, callback)


def _filename(filename):
    if (not isinstance(filename, str) or not filename.strip() or len(filename) > 128
            or not filename.isprintable() or any(char in filename for char in "/\\")
            or filename in (".", "..")):
        raise ValueError("Use a filename of 1–128 printable characters without directory separators.")


def _mime(mime):
    if not isinstance(mime, str) or re.fullmatch(r"(?:\*/\*|[A-Za-z0-9!#$&^_.+\-]+/(?:[A-Za-z0-9!#$&^_.+\-]+|\*))", mime) is None:
        raise ValueError("Use a valid MIME type.")


def pick_text(callback, *, mime="text/plain", max_bytes=MAX_DOCUMENT_BYTES):
    """Pick UTF-8 text; callback(text, error) runs on the owning thread.

    (None, None) means cancelled. Errors are plain messages, not native handles.
    """
    engine = owner()
    if not callable(callback) or type(max_bytes) is not int or not 1 <= max_bytes <= MAX_DOCUMENT_BYTES:
        raise ValueError("Use a callback and a byte limit between 1 and 8 MiB.")
    _mime(mime)
    if not engine.android:
        raise FileError("File picking is available on Android.")
    try:
        from . import android_documents
        android_documents.request("read", callback, mime, limit=max_bytes)
    except FileError:
        raise
    except Exception as error:
        raise FileError("The Android file picker could not be opened.") from error


def export_text(filename, text, callback, *, mime="text/plain"):
    """Choose a destination; callback(True, None) means written, None means cancelled."""
    engine = owner()
    _filename(filename)
    _mime(mime)
    if not callable(callback) or not isinstance(text, str) or len(text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise ValueError("Use a callback and UTF-8 text no larger than 8 MiB.")
    if not engine.android:
        raise FileError("File export is available on Android.")
    try:
        from . import android_documents
        android_documents.request("write", callback, mime, filename=filename, text=text)
    except FileError:
        raise
    except Exception as error:
        raise FileError("The Android file picker could not be opened.") from error


def poll_services():
    engine = owner()
    documents = sys.modules.get(__package__ + ".android_documents")
    if engine.android and documents is not None:
        documents.poll()


def file_request_pending():
    owner()
    documents = sys.modules.get(__package__ + ".android_documents")
    return documents is not None and documents._pending is not None


def share_file(filename, data, *, mime="application/octet-stream", subject=""):
    """Share bytes through a temporary, read-granted content URI, never file://."""
    engine = owner()
    _filename(filename)
    _mime(mime)
    if not isinstance(data, bytes) or not data or len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("Choose non-empty file bytes no larger than 8 MiB.")
    if not isinstance(subject, str) or "\0" in subject:
        raise ValueError("Use a text subject without null characters.")
    if not engine.android:
        raise ShareError("File sharing is available on Android.")
    try:
        from . import android_sharing
        android_sharing.share_file(filename, data, mime, subject, on_error=lambda error:
            engine.invoke_in_main_thread(engine.notify, "Android file sharing could not be opened."))
    except Exception as error:
        raise ShareError("Android file sharing could not be opened.") from error


def share_text(text, *, subject=""):
    """Request Android's plain-text chooser; selecting/sending stays with the user.

    Launch errors are notified on the engine thread. This asynchronous request
    does not report whether the user shared or dismissed the chooser.
    """
    engine = owner()
    if not isinstance(text, str) or not text.strip() or "\0" in text:
        raise ValueError("Choose non-empty text without null characters to share.")
    if not isinstance(subject, str) or "\0" in subject:
        raise ValueError("Use a text subject without null characters.")
    if not engine.android:
        raise ShareError("Text sharing is available on Android.")
    try:
        from . import android_sharing
        android_sharing.share_text(text, subject, on_error=lambda error:
            engine.invoke_in_main_thread(engine.notify, "Android sharing could not be opened."))
    except Exception as error:
        raise ShareError("Android sharing could not be opened.") from error


def copy_text(text):
    """Copy literal UTF-8 text through Ren'Py's existing SDL clipboard."""
    owner()
    if not isinstance(text, str) or "\0" in text:
        raise ValueError("Use text without null characters.")
    try:
        import pygame.scrap
        pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))
    except Exception as error:
        raise ClipboardError("Text could not be copied to the clipboard.") from error


def clipboard_text():
    """Read text only when requested; an empty/non-text clipboard returns ''."""
    owner()
    try:
        import pygame.scrap
        value = pygame.scrap.get(pygame.SCRAP_TEXT)
        return value.decode("utf-8").rstrip("\0") if value else ""
    except Exception as error:
        raise ClipboardError("Clipboard text could not be read.") from error


def bind(engine, *, data_directory=None):
    global _engine, _thread, _records, _data_directory
    _engine, _thread = engine, threading.get_ident()
    _records, _data_directory = {}, data_directory


def _record_path(collection):
    engine = owner()
    data_directory = _data_directory
    if data_directory is None:
        if engine.android:
            from jnius import autoclass
            activity = autoclass("org.renpy.android.PythonSDLActivity").mActivity
            data_directory = Path(str(activity.getFilesDir().getAbsolutePath())) / "renmodpy"
        else:
            data_directory = Path(engine.config.savedir) / "application-data"
    return Path(data_directory) / (collection + ".json")


def owner():
    if _engine is None or threading.get_ident() != _thread:
        raise RuntimeError("Native operations belong to the bound Ren'Py thread.")
    return _engine


def records(collection="records"):
    owner()
    if not isinstance(collection, str) or re.fullmatch(r"[a-z][a-z0-9_-]{0,47}", collection) is None:
        raise ValueError("Use a collection name of 1–48 lowercase letters, digits, underscores or hyphens.")
    if collection not in _records:
        _records[collection] = RecordStore(_record_path(collection))
    return _records[collection]


def resume_slot():
    return owner().newest_slot(r"^(renmodpy-resume|_reload-1)$")


def save_resume():
    engine = owner()
    engine.take_screenshot()
    engine.save(RESUME_SLOT, extra_info="Resume story")


def quick_available():
    return owner().can_load(QUICK_SLOT)


def save_quick():
    engine = owner()
    engine.take_screenshot()
    engine.save(QUICK_SLOT, extra_info="Quick save")


def load_quick():
    if not quick_available():
        raise ValueError("There is no quick save yet.")
    owner().load(QUICK_SLOT)


def begin_story():
    engine = owner()
    for slot in (RESUME_SLOT, "_reload-1"):
        engine.unlink_save(slot)


def finish_story(result):
    engine = owner()
    engine.store.persistent.renmodpy_last_result = str(result)
    engine.save_persistent()
    for slot in (RESUME_SLOT, "_reload-1"):
        engine.unlink_save(slot)


def valid_name(value):
    if not isinstance(value, str):
        raise ValueError("Give the save a name.")
    value = value.strip()
    if not value or len(value) > 80 or not value.isprintable():
        raise ValueError("Use a name of 1–80 printable characters.")
    return value


def _fingerprint(slot, metadata):
    engine = owner()
    return hashlib.sha256(json.dumps([engine.slot_mtime(slot), metadata],
                                    sort_keys=True).encode()).hexdigest()


def save_catalog():
    engine = owner()
    entries = []
    for slot in engine.list_slots("^" + MANUAL_PATTERN + "$"):
        if re.fullmatch(MANUAL_PATTERN, slot) is None:
            continue
        metadata = engine.slot_json(slot)
        if not isinstance(metadata, dict):
            continue
        details = metadata.get("renmodpy", {})
        supported = isinstance(details, dict) and details.get("version") == 1
        entries.append({"slot": slot, "name": metadata.get("_save_name", "Saved story"),
                        "time": engine.slot_mtime(slot),
                        "scene": details.get("scene", "") if isinstance(details, dict) else "",
                        "supported": supported, "fingerprint": _fingerprint(slot, metadata)})
    return sorted(entries, key=lambda row: row["time"] or 0, reverse=True)


def _current(slot, fingerprint):
    entry = next((row for row in save_catalog() if row["slot"] == slot), None)
    if entry is None or entry["fingerprint"] != fingerprint:
        raise ValueError("That save changed; refresh before trying again.")
    return entry


def _write_save(slot, name, scene):
    engine = owner()
    name = valid_name(name)
    engine.take_screenshot()
    engine.save(slot, extra_info=name, extra_json={
        "renmodpy": {"version": 1, "scene": str(scene), "revision": uuid.uuid4().hex}})


def create_save(name, scene="Story"):
    slot = "renmodpy-manual-" + uuid.uuid4().hex
    _write_save(slot, name, scene)
    return slot


def overwrite_save(slot, fingerprint, name, scene="Story"):
    _current(slot, fingerprint)
    _write_save(slot, name, scene)


def delete_save(slot, fingerprint):
    _current(slot, fingerprint)
    owner().unlink_save(slot)


def load_save(slot, fingerprint):
    entry = _current(slot, fingerprint)
    if not entry["supported"]:
        raise ValueError("This save format is unsupported.")
    owner().load(slot)
