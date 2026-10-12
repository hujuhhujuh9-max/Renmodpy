# Source provenance

RenModPy is an Android-only modified Ren'Py distribution. This first import
uses the owner's SDK- repository as a donor and does not modify that repository.

Donor main commit: `0fc79f001b2177a9a31dea31fd781b4cc298a510`.

| Destination | Donor | Adaptation |
| --- | --- | --- |
| `engine/python/renmodpy/tactics.py` | `runtime/tactics.py` | Model retained |
| `engine/python/renmodpy/board.py` | `game/tactics_display.py` | Direct BoardSession ownership; Flet/shared bridge removed |
| `engine/python/renmodpy/board_session.py` | `runtime/renfletpy.py` | Native-only board controller and versioned save state |
| `engine/python/renmodpy/records.py` | `runtime/application_data.py` | Record validation/identity adapted; atomic file replaces Flet preferences |
| `engine/python/renmodpy/forms.py` | `runtime/form_list.py`, `docs/form-list.md` | Reusable form/draft recovery behavior implemented with native screen inputs |
| `engine/python/renmodpy/services.py` | `runtime/save_slots.py` | Native named-save behavior adapted; no Flet command transport |
| `engine/python/renmodpy/android_jni*.py` | `runtime/android_jni*.py` | JNI helpers retained; executor import made relative |
| `prepare.py` | `prepare.py` | Preparation restricted to Ren'Py and RAPT |
| `tests/test_tactics.py` | `tests/test_tactics.py` | Terrain/camera regression cases retained |
| `.github/workflows/validate.yml`, `scripts/check_android.py` emulator setup | `.github/workflows/check-project-update.yml` at `0fc79f001b2177a9a31dea31fd781b4cc298a510` | Direct SDK/AVD startup and first-use setup adapted to the native validation APK; no emulator action runtime |

Native history, reading settings, quick save/load and replay reproduce the
donor's `runtime/story_ui.py` behavior using Ren'Py's own history, preferences,
save system and restart path. The form draft/controller contains ordinary data;
RecordStore ownership remains outside story saves.

Clipboard copy/read reproduces SDK-'s `runtime/capability_demo.py` clipboard
behavior at donor commit `0fc79f001b2177a9a31dea31fd781b4cc298a510`, using
Ren'Py's existing SDL clipboard API instead of Flet's service. Native Records
and history supply copy/paste actions; their UTF-8 encoding follows Ren'Py's
`CopyToClipboard` implementation in the locked Ren'Py component. Paste appends
to the selected draft field and validates it before changing that field.

Text sharing in `engine/python/renmodpy/android_sharing.py` uses Android's
existing `ACTION_SEND`/`ACTION_CHOOSER` Intents with `text/plain`, behind the
engine's Python services API. Its concrete use case is exporting visible saved
Records and plain dialogue lines from the same story/app session. The UI-thread
dispatcher extends the retained donor `android_jni.py` callback from
`0fc79f001b2177a9a31dea31fd781b4cc298a510`, retaining the native proxy until its
Android callback returns and reporting errors through Ren'Py's thread queue.
Android platform calls replace the donor's Flet sharing transport. The donor's
`runtime/capability_demo.py` exercises file sharing; this addition covers text
and does not establish parity for its file picker or attachment operation.

`engine/patches/startup-load-boundary.patch` corrects the donor's removal of
startup save boundaries in `renpy/savestate.py` and `renpy/common/00start.rpy`.
Those files originate in the locked Ren'Py component commit
`0d58d1fc5b5fed87cb0f54eb717233d05643f506`. The patch retains the original
notices and uses the existing `not_greedy` load-frame flag to prevent restoring
past initialized history/defaults when saving on the first dialogue. It adds
no player rollback API or rewind history. Host and Android acceptance exercise
ordinary main-menu startup and cold Resume of that first interaction.

`engine/patches/mobile-recovery-preservation.patch` changes mobile recovery
cleanup in the same locked component's `renpy/display/core.py`. A cold Home
does not create a background save; returning to it must therefore keep the
previous process's pending `_reload-1` checkpoint. The patch skips cleanup
under the same main-menu/replay conditions that skip mobile saving. Returning
normally to a live story still clears its temporary background checkpoint.
This preserves the donor's documented background recovery behavior using the
existing native save handler and RenModPy Home, with no additional service or
Android host changes.

`engine/patches/mobile-suspend-before-render.patch` prioritizes pending SDL
suspend events before renderer resize/redraw in that component's same native
interaction loop. Android acceptance exposed a missing-current-GL-context
shader error while backgrounding Records with the keyboard open, before the
ordinary event handler could write its recovery save. The patch runs the
existing suspend/save/wait/foreground handler first, preserving its normal
display-reset path. Host fixtures inject SDL suspend/foreground events and
verify their ordering before redraw; Android acceptance exercises the actual
surface and keyboard lifecycle.

The tactics model and renderer were originally adapted by SDK- from the
owner's 2d-test commit `7dc24c50ef8900ede31dd4bcdc01422b55d5addb`.

`sdk-lock.json` pins the modified Ren'Py 8.5.3 and RAPT component commits,
archive checksums, and the null activity-result patch. Player rollback is
already removed in the donor Ren'Py archive. Its patch must not be reapplied.
The Flutter-specific FragmentActivity patch is not part of this first import.

Original project notices remain in LICENSE. Ren'Py, SDL, Python, and other
third-party code retain their existing notices in the assembled SDK. No
third-party material is relicensed by this project.
