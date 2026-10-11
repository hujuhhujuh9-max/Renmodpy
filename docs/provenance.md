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

`engine/patches/startup-load-boundary.patch` corrects the donor's removal of
startup save boundaries in `renpy/savestate.py` and `renpy/common/00start.rpy`.
Those files originate in the locked Ren'Py component commit
`0d58d1fc5b5fed87cb0f54eb717233d05643f506`. The patch retains the original
notices and uses the existing `not_greedy` load-frame flag to prevent restoring
past initialized history/defaults when saving on the first dialogue. It adds
no player rollback API or rewind history. Host and Android acceptance exercise
ordinary main-menu startup and cold Resume of that first interaction.

The tactics model and renderer were originally adapted by SDK- from the
owner's 2d-test commit `7dc24c50ef8900ede31dd4bcdc01422b55d5addb`.

`sdk-lock.json` pins the modified Ren'Py 8.5.3 and RAPT component commits,
archive checksums, and the null activity-result patch. Player rollback is
already removed in the donor Ren'Py archive. Its patch must not be reapplied.
The Flutter-specific FragmentActivity patch is not part of this first import.

Original project notices remain in LICENSE. Ren'Py, SDL, Python, and other
third-party code retain their existing notices in the assembled SDK. No
third-party material is relicensed by this project.
