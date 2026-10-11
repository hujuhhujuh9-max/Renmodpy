"""Native record forms, adapted from SDK-'s reusable form/list behavior.

Drafts contain ordinary data only. The owning screen supplies its current
RecordStore for each operation; stores and their locks never enter story saves.
"""

from dataclasses import dataclass

from .records import RecordsError


@dataclass(frozen=True)
class FormField:
    name: str
    label: str
    required: bool = False
    multiline: bool = False
    max_length: int = 1000

    def __post_init__(self):
        if (not isinstance(self.name, str) or not self.name.strip()
                or len(self.name) > 80 or not self.name.isprintable()
                or not isinstance(self.label, str) or not self.label.strip()
                or len(self.label) > 200
                or type(self.required) is not bool or type(self.multiline) is not bool
                or type(self.max_length) is not int or not 1 <= self.max_length <= 4096):
            raise ValueError("Invalid record field.")


DEFAULT_FIELDS = (FormField("title", "Title", required=True, max_length=80),
                  FormField("body", "Note", multiline=True))


class RecordDraft:
    def __init__(self, fields=DEFAULT_FIELDS):
        self.fields = tuple(fields)
        if (not 1 <= len(self.fields) <= 32
                or any(not isinstance(field, FormField) for field in self.fields)
                or len({field.name for field in self.fields}) != len(self.fields)):
            raise ValueError("Use 1–32 uniquely named record fields.")
        self.values = {field.name: "" for field in self.fields}
        self.cancel()

    def cancel(self):
        # Keep this dictionary's identity: native InputValues refer to it.
        self.values.update((field.name, "") for field in self.fields)
        self.editing_id = None
        self.revision = None
        self._original = {}
        self.needs_reload = False
        self.message = ""

    def edit(self, snapshot, identifier):
        row = next((row for row in snapshot["records"] if row["id"] == identifier), None)
        if row is None:
            raise RecordsError("That record no longer exists. Reload to continue.")
        self.editing_id = identifier
        self.revision = snapshot["revision"]
        self._original = dict(row["values"])
        self.values.update((field.name, row["values"].get(field.name, "")) for field in self.fields)
        self.needs_reload = False
        self.message = "Editing record. Cancel keeps the saved version."

    def reload(self, snapshot):
        if self.editing_id is not None:
            row = next((row for row in snapshot["records"] if row["id"] == self.editing_id), None)
            if row is None:
                self.editing_id = None
                self._original = {}
                self.message = "The record was deleted. Your draft is kept; add it as a new record."
            else:
                self._original = dict(row["values"])
                self.message = "Records refreshed. Your draft is kept."
            self.revision = snapshot["revision"]
        else:
            self.message = "Records refreshed. Your draft is kept."
        self.needs_reload = False

    def submit(self, records, revision):
        if self.needs_reload:
            self.message = "Reload records before saving. Your draft is kept."
            return False
        try:
            values = dict(self._original)
            for field in self.fields:
                value = self.values[field.name]
                if not isinstance(value, str):
                    raise ValueError("Use text for " + field.label + ".")
                value = value.strip()
                if field.required and not value:
                    raise ValueError("Enter " + field.label + ".")
                if len(value) > field.max_length:
                    raise ValueError(field.label + " is too long.")
                values[field.name] = value
            if self.editing_id is None:
                records.create(values, expected_revision=revision)
            else:
                records.update(self.editing_id, values, expected_revision=self.revision)
        except RecordsError as error:
            self.needs_reload = True
            self.message = str(error) + " Reload records; your draft is kept."
            return False
        except ValueError as error:
            self.message = str(error)
            return False
        self.cancel()
        self.message = "Record saved."
        return True
