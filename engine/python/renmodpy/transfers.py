"""Versioned Records backups; preview first and merge only on confirmation."""

import copy
import json
import uuid

from .records import validate_values

MAX_DOCUMENT_BYTES = 8 * 1024 * 1024


def validate_rows(rows):
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError("Use a backup with at most 1,000 records.")
    identifiers = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "values"}:
            raise ValueError("The backup contains an invalid record.")
        identifier = row["id"]
        try:
            valid = isinstance(identifier, str) and len(identifier) == 32 and uuid.UUID(hex=identifier).hex == identifier
        except ValueError:
            valid = False
        if not valid or identifier in identifiers:
            raise ValueError("The backup contains an invalid or duplicate record identity.")
        identifiers.add(identifier)
        validate_values(row["values"])
        if any("\0" in key or "\0" in value for key, value in row["values"].items()):
            raise ValueError("Backup fields cannot contain null characters.")
    return copy.deepcopy(rows)


def dump_records(snapshot):
    rows = validate_rows(snapshot["records"])
    text = json.dumps({"type": "renmodpy.records", "version": 1, "records": rows},
                      ensure_ascii=False, indent=2) + "\n"
    if len(text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise ValueError("This backup exceeds the 8 MiB document limit.")
    return text


def load_records(text):
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise ValueError("Choose a UTF-8 Records backup no larger than 8 MiB.")
    try:
        data = json.loads(text.removeprefix("\ufeff"))
    except ValueError as error:
        raise ValueError("This file is not a valid JSON backup.") from error
    if (not isinstance(data, dict) or set(data) != {"type", "version", "records"}
            or data["type"] != "renmodpy.records" or type(data["version"]) is not int or data["version"] != 1):
        raise ValueError("This Records backup format is unsupported.")
    return validate_rows(data["records"])


def preview_records(rows, snapshot):
    rows = validate_rows(rows)
    current = {row["id"]: row["values"] for row in snapshot["records"]}
    for row in rows:
        if row["id"] in current:
            validate_values(dict(current[row["id"]], **row["values"]))
    added = sum(row["id"] not in current for row in rows)
    updated = sum(row["id"] in current and dict(current[row["id"]], **row["values"]) != current[row["id"]]
                  for row in rows)
    if len(current) + added > 1000:
        raise ValueError("Importing would exceed 1,000 records.")
    return {"new": added, "updated": updated, "unchanged": len(rows) - added - updated,
            "revision": snapshot["revision"]}
