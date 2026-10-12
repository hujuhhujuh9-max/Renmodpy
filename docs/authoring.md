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
