"""Native services owned by the Ren'Py thread, outside story snapshots."""

import hashlib
import json
import os
import re
import threading
import uuid
from pathlib import Path

from .records import RecordStore


RESUME_SLOT = "renmodpy-resume"
QUICK_SLOT = "renmodpy-quick"
MANUAL_PATTERN = r"renmodpy-manual-[0-9a-f]{32}"
_engine = None
_thread = None
_records = {}
_data_directory = None


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
