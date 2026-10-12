# Codex handoff

RenModPy's native app/story foundation now passes Android emulator acceptance.
Read [vision.md](vision.md), [user-prompts.md](user-prompts.md) and `AGENTS.md`
before continuing. The product remains one continuous Android-only modified
Ren'Py application, with SDK-/RenFletPy as the quality benchmark.

The user clarified the niche as "Ren'Py++": modified Ren'Py with focused
additions for Python stories, visual novels and integrated Android app screens.
Godot's broader general-purpose engine scope remains outside the roadmap.
Apply later user corrections when interpreting voice-transcription errors.

## Where the work is

- Repository: `hujuhhujuh9-max/Renmodpy`.
- Review branch: `bootstrap/native-foundation`.
- Draft review: [PR #1](https://github.com/hujuhhujuh9-max/Renmodpy/pull/1).
- Verified engine/test revision: `aadefd6f421bfa0163fa187abfbdfdc8a06501f0`.
- Donor benchmark: SDK- `0fc79f001b2177a9a31dea31fd781b4cc298a510`.
- Locked Ren'Py component: `0d58d1fc5b5fed87cb0f54eb717233d05643f506`.
- Ren'Py/RAPT archives, checksums and notices remain pinned in `sdk-lock.json`.

The user renewed work in Codex and asked RenModPy to carry forward SDK-'s
strengths. Their README vision addition is retained, and the continuation
prompt is preserved verbatim. Work remains on the draft branch; no merge or
application release has been requested.

## Implemented and verified

The assembled SDK includes native Home/Return/Resume, named checkpoints,
quick saves, story history, persistent reading settings, full story replay and
editable Records. Forms support custom fields, independent collections,
multiline input, stale-edit protection and draft recovery. Application Records
remain independent of story snapshots. Tactics remains a regression example.

The 2026-10-12 continuation adds native clipboard copy/read to the engine's
services API. Records can copy their visible fields and append clipboard text
to draft fields; history can copy a dialogue line without formatting tags.
Unicode and multiline Note paste are supported. Invalid or oversized input
keeps the draft unchanged and never writes a record. Stale edits still require
Reload before saving. Production clipboard reads occur only after Paste is
requested, and all operations run on Ren'Py's owning thread through SDL.

The [completed CI run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38195036572)
passes all three jobs at the verified revision:

- 50 Python state/storage/form/build/clipboard tests.
- Real engine compile/lint, rendered menus, record editing, named saves,
  quick load, replay, Android distribution-input checks and the new ordinary
  startup/first-dialogue cold-load regression with both Linux renderers.
  Both renderers also pass SDL clipboard round trips and plain history export.
- RAPT APK compilation and real Android interaction on a rooted Android 15 /
  API 35 x86_64 emulator, at 720×1280 and 160 dpi.

The Android harness drives ADB taps and keyboard events; its APK observer only
reports state. The seven completed acceptance checks cover:

1. Home/history/settings/Records navigation and Return to the waiting dialogue.
2. Force-stop/relaunch and durable Resume of the first dialogue, with Records
   and newer reading preferences intact.
3. A story choice followed by Quick load restoring the earlier dialogue and
   clearing that choice without rewinding Records or reading settings.
4. Native save-name input, checkpoint creation, confirmed overwrite, another
   process restart and confirmed named-load of the chosen dialogue.
5. Replay clearing story history/choice state while keeping application
   Records, reading settings, quick and named checkpoints.
6. Cancelled deletion retaining the checkpoint and confirmed deletion removing
   only that checkpoint.
7. Native history/record copy, Unicode/multiline paste and rejected Title paste
   preserving the draft. Copied clipboard contents and pasted Records remain
   current through cold restart, older-save loading and replay.

The new Records screenshots show the pasted accented, multiline lighthouse
note and the copied saved record. The earlier foundation run captured the
Android software keyboard during entry.
Menu headings now fit their reserved width, including with larger text, and
the save-name field can be deselected to close the keyboard.

## Evidence and validation APK

The latest receipts, APK checksum and engine/example input hashes are
preserved in [android-clipboard-acceptance.json](android-clipboard-acceptance.json).
The earlier [foundation receipt](android-acceptance.json) remains unchanged. Downloaded CI
input hashes were compared with the review code and match. Later documentation
updates do not change those engine/example inputs.

- [Android job and log](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38195036572/job/114635711451)
- [Android state, screenshots, logcat and build receipt](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38195036572/artifacts/11723525771)
- [Disposable validation APK and checksum receipt](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38195036572/artifacts/11723176887)
- [Both native renderer receipts and screenshots](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38195036572/artifacts/11722099205)

The artifact retention period is 14 days, expiring on 2026-10-26. The committed
receipt remains available after the downloadable artifacts expire.

The APK is `org.renmodpy.example-0.1.0-1791771382-release.apk`, targeting API 36.
Its SHA-256 is
`20fda9c62c7895117b2d56616d2a6ee23494e1548d20ed6e63d83483bff4f295`.
Despite RAPT's filename, this is a disposable test fixture with a temporary
signing key and read-only observer; the build receipt marks `release: false`.

## Blockers resolved during continuation

The earlier [Android attempt](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38176677164)
built an APK but failed before emulator boot because the emulator action could
not import `@actions/core`. The previous session stopped there as requested.
Codex replaced that action with SDK-'s direct SDK/AVD startup and first-use
setup, and removed the redundant review-branch push run.

The [first booted emulator run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38177385705)
then exposed a cold Resume crash: loading a save on the first dialogue restored
past initialized history/defaults. Logcat reported `_history` missing, followed
by an observer error for `_history_list`. A normal-startup host reproduction
also failed by re-executing defaults. Existing probes skipped the main menu and
saved after completed interactions, so they had not covered this path.

`engine/patches/startup-load-boundary.patch` restores the required startup save
boundaries using the existing load-frame flag. Assembly applies it to the
locked donor source, removes the stale compiled startup script and records its
hash. Player rollback remains removed. New native and Android regressions now
pass this previously failing path.

The older handoff reported an intermittent local deleted-save discrepancy.
The complete current local native run and both clean CI renderer runs pass the
same deletion checks; no speculative filesystem change was made.

## Continue from this foundation

Use [feature-parity.md](feature-parity.md) for capability gaps. Physical-device
and ARM acceptance, Unicode IME composition, rotation/background recovery,
board touch/camera acceptance, other Android service operations, AAB packaging and
same-key updates remain unverified. Audio/video/ATL and richer app controls
still need representative native fixtures or implementation. The x86_64
emulator pass establishes the seven checks above, not full RenFletPy parity.

Keep Ren'Py/SDL as the startup/rendering/story/Python owner. Added functionality
belongs in the engine's Python API, common screens or native Android support.
Keep application data independent of story saves and keep the existing camera,
location, recording and rollback choices.

Build setup and commands are in [build-environment.md](build-environment.md).
Local commands require Linux x86_64, Python 3.12+, JDK 21, Android SDK platform
36/build-tools 36, `adb` and an emulator; CI supplies KVM. The native check can
run without an Android device. SDK assembly requires a fresh output directory,
and the ADB harness must only target a disposable rooted emulator. Preserve
evidence if a new environment blocker prevents further acceptance.
