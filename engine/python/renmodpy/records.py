"""Application records independent of Ren'Py story checkpoints.

Validation and record identity are adapted from SDK-/runtime/application_data.py.
The Flet preferences transport is replaced with an atomic private JSON file.
One RecordStore owns a file; concurrent writes from separate processes are
outside this initial contract.
"""

import copy
import json
import os
import tempfile
import threading
import uuid
from pathlib import Path


class RecordsError(RuntimeError):
    pass


def validate_values(values):
    if (not isinstance(values, dict) or not values or len(values) > 32
            or any(not isinstance(k, str) or not k.strip() or len(k) > 80
                   or not isinstance(v, str) or len(v) > 4096
                   for k, v in values.items())):
        raise ValueError("Records require 1–32 named text fields.")
    return dict(values)


class RecordStore:
    def __init__(self, path):
        self.path = Path(path)
        self._lock = threading.RLock()

    def _read(self):
        if not self.path.exists():
            return {"version": 1, "revision": 0, "records": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if (not isinstance(data, dict) or set(data) != {"version", "revision", "records"}
                    or type(data["version"]) is not int or data["version"] != 1
                    or type(data["revision"]) is not int or data["revision"] < 0
                    or not isinstance(data["records"], list) or len(data["records"]) > 1000):
                raise ValueError("Unsupported records file")
            ids = set()
            for row in data["records"]:
                if (not isinstance(row, dict) or set(row) != {"id", "values"}
                        or not isinstance(row["id"], str)
                        or len(row["id"]) != 32 or uuid.UUID(hex=row["id"]).hex != row["id"]
                        or row["id"] in ids):
                    raise ValueError("Invalid record identity")
                validate_values(row["values"])
                ids.add(row["id"])
            return data
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise RecordsError("Records could not be read; the file was preserved.") from error

    def snapshot(self):
        with self._lock:
            return copy.deepcopy(self._read())

    def list(self):
        return self.snapshot()["records"]

    def _write(self, data):
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                             dir=self.path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except OSError as error:
            raise RecordsError("Records could not be saved.") from error
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _mutate(self, operation, expected_revision=None):
        with self._lock:
            data = self._read()
            if expected_revision is not None and data["revision"] != expected_revision:
                raise RecordsError("Records changed; refresh before editing.")
            operation(data["records"])
            data["revision"] += 1
            self._write(data)
            return copy.deepcopy(data)

    def create(self, values, *, expected_revision=None):
        values = validate_values(values)
        identifier = uuid.uuid4().hex

        def append(rows):
            if len(rows) >= 1000:
                raise RecordsError("This collection already has 1,000 records.")
            rows.append({"id": identifier, "values": values})

        self._mutate(append, expected_revision)
        return identifier

    def update(self, identifier, values, *, expected_revision=None):
        values = validate_values(values)

        def edit(rows):
            row = next((r for r in rows if r["id"] == identifier), None)
            if row is None:
                raise RecordsError("That record no longer exists.")
            row["values"] = values

        return self._mutate(edit, expected_revision)

    def delete(self, identifier, *, expected_revision=None):
        def remove(rows):
            row = next((r for r in rows if r["id"] == identifier), None)
            if row is None:
                raise RecordsError("That record no longer exists.")
            rows.remove(row)

        return self._mutate(remove, expected_revision)
