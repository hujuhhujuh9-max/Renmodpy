# One app and story project

Use the assembled RenModPy SDK to author an ordinary Ren'Py project. The
engine already contains the built-in app screens and Python services. Project
screens, stories and assets belong in the project's usual `game/` directory.

The portrait example uses a 720×1280 canvas. Its main menu embeds the engine's
Home screen, while dialogue and Android Back open Home in a menu context:

```renpy
define config.screen_width = 720
define config.screen_height = 1280
define config.game_menu_action = ShowMenu("renmodpy_home")

init python:
    from renpy.renmodpy import services as app

screen main_menu():
    tag menu
    use renmodpy_home(story_label="start")

label main_menu:
    call screen main_menu
    return

label start:
    $ app.begin_story()
    $ renmodpy_scene = "The lighthouse"
    "Mira" "Someone left a folded note at the lighthouse."
    $ app.finish_story("The lighthouse note is complete.")
    return
```

`begin_story()` clears old Resume/recovery bookmarks. `finish_story(result)`
records the completion result and clears them again. Quick saves, named saves,
Records and reading preferences remain available. Replay uses the engine's
full restart path so project `default` variables and history reset correctly.

Home writes a resume bookmark when opened through the example's dialogue,
choice and activity buttons. Returning from its menu context continues the
same waiting story interaction. Loading a checkpoint restores native script
position and saveable project state, then reads current application data and
preferences.

Android's existing SDL suspend handler writes a native recovery checkpoint
when an active story is backgrounded. If Android kills that process, the next
Home offers the newest recovery or explicit Resume bookmark. Switching away
from that cold Home before pressing Resume preserves the recovery checkpoint.
Returning normally to the still-running story keeps the live session and
clears its temporary recovery file. Starting/replaying or completing a story
clears both kinds of Resume bookmark through `begin_story()`/`finish_story()`.
Quick and named saves are independent.

A Records draft stays in its live menu during a normal app switch. Submit a
record to persist it across process death; recovering a story restores the
waiting story interaction, while saved Records and reading preferences remain
current. `config.save_on_mobile_background` controls the underlying Ren'Py
recovery save and defaults to enabled.

## Reusable Records

`ShowMenu("renmodpy_records")` opens the default Title/Note collection.
Projects can select another collection, title and field schema:

```renpy
init python:
    from renpy import renmodpy
    field_note_fields = (
        renmodpy.FormField("title", "Title", required=True, max_length=80),
        renmodpy.FormField("notes", "Notes", multiline=True, max_length=2000),
    )

screen field_note_link():
    textbutton "Field notes" action ShowMenu("renmodpy_records",
        collection="field-notes", title="Field notes", fields=field_note_fields)
```

The screen supports add/edit/cancel/delete/reload. Edits preserve stored fields
outside the visible schema. Required and length errors keep the draft. Failed
or stale writes block more submissions until Reload succeeds; Reload keeps
the draft, including when a deleted record must become a new Add operation.

`app.records("field-notes")` exposes the same `RecordStore` to project Python.
Collection names use 1–48 lowercase letters, digits, underscores or hyphens,
starting with a letter. Each collection has a private JSON file. The default
continues using `records.json`. Android uninstall/clear-data removes these files.

## Custom activities and saving

Use native screens/labels/displayables for project activities. Store their
plain state in project `default` variables or versioned saveable Python
objects. Render caches, services, worker handles and locks stay outside saved
state. The included board is one example of this contract.

Engine flow/save operations run on Ren'Py's owning thread; Android view work
runs on Android's UI thread. Projects choose fonts and assets suitable for
their text. The standard/larger reading setting uses Ren'Py's native font-size
preference and applies to native screens as well as dialogue.

Records fields and the named-checkpoint field can be tapped to enable or
disable editing. Deselecting the input closes Android's keyboard so the screen
actions are available. Menu headings wrap within their allotted width,
including when the larger reading preference is selected.

## Copy and paste

Each Records field has a Paste button. It appends plain clipboard text to the
end of that field, leaving the other fields unchanged. The Note field accepts
Unicode and line breaks; single-line fields reject line breaks. Empty text,
invalid text or a result exceeding the field limit leaves the draft intact.
Pasting does not save a record or clear a stale-edit/reload requirement.

Copy record exports only fields visible in the current schema, separated by
blank lines. Literal braces and brackets are retained; hidden stored fields
are excluded. Story history's Copy line exports the dialogue without Ren'Py
formatting tags. The sample's lighthouse note includes an accented place name
and a line break to demonstrate this flow.

Project Python can use the same SDL clipboard through the owning Ren'Py thread:

```python
from renpy.renmodpy import services as app

app.copy_text("Blåbær\nLiteral {note} [value]")
text = app.clipboard_text()  # Empty/non-text clipboard returns an empty string.
```

`app.ClipboardError` reports a platform/backend failure. Production screens
read the clipboard only after Paste is requested. Clipboard contents belong
to the operating system and remain outside story saves, alongside the current
application data; loading or replaying a story does not restore older clipboard
contents. These operations use the engine's existing clipboard implementation
and add no Android permissions or additional UI runtime.

## Share text on Android

History offers Share line and saved Records offer Share record on Android.
They open Android's system chooser with plain text. Record exports include only
the visible saved fields, separated by blank lines; an unsaved form draft is
kept. History exports remove Ren'Py formatting tags. Unicode and line breaks
are retained. Dismissing the chooser returns to the same live menu and waiting
story; sharing does not submit a record or change a checkpoint or clipboard.
The form input stays inactive on return; tap a field to continue editing.

Project Python can request the same chooser on Ren'Py's owning thread:

```python
from renpy.renmodpy import services as app

app.share_text("Blåbær\nLiteral {note} [value]", subject="Field notes")
```

The request is asynchronous. Android view operations run on its UI thread
through the engine's existing JNI callback, while SDL continues to handle
suspend/foreground events. A queued native proxy is retained until it finishes
and is never part of a story save. The return value does not report whether
the chooser was dismissed or a receiving app sent anything.

Empty/non-text or null-containing values raise `ValueError`. Unsupported
platforms or immediate dispatch failures raise `app.ShareError`; a later UI
launch failure is notified on Ren'Py's thread. The built-in screens keep the
draft on failures.

## Documents and Records backups

`app.pick_text(callback, mime="text/plain", max_bytes=8388608)` opens Android's
document picker. `app.export_text(filename, text, callback, mime="text/plain")`
opens its save picker. The callback receives `(value, error)` on Ren'Py's owning
thread: selected UTF-8 text or `True` after a completed write; `(None, None)`
means cancellation. An error is a plain message. Invalid arguments raise
`ValueError`; unavailable platforms or immediate launch failures raise
`app.FileError`. Only one picker request may be active. Native document IO runs
on a class-loader-bound worker, and native objects/callbacks never enter saves.
The engine polls activity results automatically. Pickers use scoped content
URIs and need no broad external-storage permission. UTF-8 documents are bounded
at 8 MiB; invalid encoding is rejected without changing Records or the draft.

Built-in Android Records offers Import backup, Export backup and Share backup.
The version-1 JSON backup includes IDs and every saved field, including fields
omitted by the current form. It excludes the local concurrency revision and
unsaved drafts. Imports first show new/updated/unchanged counts. Only **Import
these records** commits the merge. Matching IDs update supplied fields while
keeping omitted fields; unrelated rows remain. A stale preview must be refreshed
before confirmation. An edited row requires Reload after an import, preserving
the draft until the user chooses how to proceed.

`renpy.renmodpy.transfers.dump_records(store.snapshot())`, `load_records(text)`
and `preview_records(snapshot, rows)` expose this versioned format. Apply an
approved candidate with `store.merge(rows, expected_revision=snapshot["revision"])`.
The merged collection is validated and written atomically. Imported IDs must be
canonical 32-character UUID hex; collections allow at most 1,000 rows and each
row at most 32 text fields. Backups from SDK-'s Flet preferences require an
explicit conversion; they are not silently treated as this format.

Saved order and the first field's A–Z control change only the displayed row
order. Alphabetical sorting is case-insensitive, retains record identities and
does not write the collection, reset the draft or change the current edit.

`app.share_file(filename, data, mime="application/octet-stream", subject="")`
shares non-empty bytes up to 8 MiB through Android's chooser and a temporary
cache-backed content URI with a read grant. Filenames are printable basenames
of 1–128 characters. Share errors follow the same immediate/queued behavior as
text sharing. The API does not report receiving-app delivery. Old export cache
directories are removed after 24 hours on a subsequent attachment request.

## Private text and touch feedback

`app.secure_set(key, text, callback)`, `secure_get(key, callback)` and
`secure_delete(key, callback)` use Android Keystore AES-GCM on Android 6/API 23
or later. Keys are printable names of 1–128 characters; text is bounded at
64 KiB UTF-8. Callbacks run on the engine owner and receive `(value, error)`.
Set returns `True` after atomic commit; get returns text or `None` when absent;
delete returns whether the entry existed. Authentication/read failures return
an error and preserve the encrypted bytes and existing key. Request failures
raise `app.StorageError`, and argument errors raise `ValueError`.

Encrypted entries live in the application's no-backup directory, independently
of Records and story saves. The key name is authenticated with the ciphertext.
Hardware-backed encryption depends on the device; emulator acceptance does not
establish hardware protection. Keep decrypted values out of `default`,
`persistent`, story variables, backups, logs and diagnostics. A Python module's
private state can hold a value for the current process without saving it.
Uninstall/data clearing removes the app's entries and Keystore key.

`app.haptic("selection", callback=None)` and `app.haptic("confirm", callback=None)`
request the platform's native touch feedback on the UI thread. An optional
callback receives an accepted boolean or an error. Acceptance does not prove
felt vibration, which depends on device hardware and settings. Records requests
confirmation feedback after a successful submit.

## Project menus and media

Projects can add Home destinations with plain pairs of captions and screen names:

```renpy
define renmodpy_home_links = (("Notes", "my_notes"),)
```

The example's Media room uses `Play`/`Stop`, `Movie` and an ATL transform on
ordinary native Ren'Py channels. Leaving it stops playback without changing the
waiting story. Its tone and color video are original generated assets; no
additional renderer, service or animation runtime is required.

## Links to saved Records

Set `"renmodpy_deep_links": true` in the project's `.android.json` before
building. The bundled example and project template enable this demonstration;
omitting the setting or setting it to `false` removes the VIEW/BROWSABLE filter
and disables native delivery. Rebuild the APK after changing it.

`app.record_link(identifier)` returns a link to a saved Record in the default
`records` collection. The built-in Records screen also offers **Copy link**.
The scheme is the application's Android package, with any underscore changed
to `+` because underscores are invalid in URI schemes. For example:

```text
org.example.story://records/0123456789abcdef0123456789abcdef
```

Opening this link shows a read-only preview of the current saved Title/Note
over the existing screen. Close or Android Back returns to that screen with
its unsaved form and waiting story kept; form input stays inactive. A cold
launch previews over Home, where Resume remains an explicit user action.
Missing/deleted Records show an unavailable message. Custom collections and
custom form schemas are outside this initial route; preview fields use
`renmodpy.DEFAULT_FIELDS` and never expose hidden fields.

Only canonical, case-sensitive package links with exactly one 32-character
lowercase hexadecimal ID are accepted. Other schemes, paths, query strings,
fragments, encoded characters and non-VIEW Intents are ignored. Links cannot
choose a story label, checkpoint, file or operation, and never write Records.
They reference data already on that installation; copying a link does not
export its contents or make it work on a different installation.

The Android activity captures initial and new Intents into one synchronized
pending text slot. Ren'Py consumes it on its owning thread; the newest
undelivered valid link wins. Polling never replays `getIntent()`. Loading a
story checkpoint dismisses any saved preview so a consumed link cannot reopen
from a background save. This is a custom URI scheme, not a verified HTTPS
Android App Link; it has no domain ownership or browser association setup.
