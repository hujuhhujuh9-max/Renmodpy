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
- Verified engine/test revision: `8f472f062ec8111f38d8af7d516752e06f8f4c40`.
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

The later lifecycle continuation preserves the newest native background
checkpoint when a freshly reopened Home is backgrounded before Resume. It
also handles queued/buffered SDL suspend events before renderer resize/redraw,
fixing the crash when switching apps with the keyboard open, discovered by the emulator.
Normal app switching retains the live Records draft and story session;
background process kills recover the waiting story choice or later dialogue.
Submitted Records and reading settings remain current.

The [completed CI run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38199188437)
passes all three jobs at the verified revision:

- 50 Python state/storage/form/build/clipboard tests.
- Real engine compile/lint, rendered menus, record editing, named saves,
  quick load, replay, Android distribution-input checks and the new ordinary
  startup/first-dialogue cold-load regression with both Linux renderers.
  Both renderers also pass SDL clipboard round trips and plain history export.
  Each passes 25 checks, including three-process choice/dialogue recovery and
  queued/buffered SDL suspend events handled before renderer redraw.
- RAPT APK compilation and real Android interaction on a rooted Android 15 /
  API 35 x86_64 emulator, at 720×1280 and 160 dpi.

The Android harness drives ADB taps and keyboard events; its APK observer only
reports state. The ten completed acceptance checks cover:

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
8. Android system Home/foreground return with the Records keyboard active,
   preserving the live draft, waiting story and preferences without submitting
   a record; the temporary recovery file is cleared on normal return.
9. Android system Home, stopped-activity confirmation, background process kill
   and cold Resume recovering the waiting choice. Switching apps again from
   that cold Home preserves the pending recovery file byte-for-byte.
10. Another background process kill and Resume recovering the later chosen
    dialogue, newer than the explicit Home/quick saves, with current Records
    and reading preferences intact.

The lifecycle screenshots show the retained Records draft and recovered
choice/dialogue. Records screenshots also show the pasted accented, multiline
lighthouse note and the copied saved record. The earlier foundation run captured the
Android software keyboard during entry.
Menu headings now fit their reserved width, including with larger text, and
the save-name field can be deselected to close the keyboard.

## Evidence and validation APK

The latest receipts, APK checksum and engine/example input hashes are
preserved in [android-lifecycle-acceptance.json](android-lifecycle-acceptance.json).
The earlier [clipboard](android-clipboard-acceptance.json) and
[foundation](android-acceptance.json) receipts remain unchanged. Downloaded CI
input hashes were compared with the review code and match. Later documentation
updates do not change those engine/example inputs.

- [Android job and log](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38199188437/job/114648542071)
- [Android state, screenshots, stopped activity, logcat and build receipt](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38199188437/artifacts/11724329932)
- [Disposable validation APK and checksum receipt](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38199188437/artifacts/11724788405)
- [Both native renderer receipts and screenshots](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38199188437/artifacts/11724812924)

The artifact retention period is 14 days, expiring on 2026-10-26. The committed
receipt remains available after the downloadable artifacts expire.

The APK is `org.renmodpy.example-0.1.0-1791775151-release.apk`, targeting API 36.
Its SHA-256 is
`236f41914ff8bb7a241fbd373c10efc6fb58e95f8d7b6d90dc016d7ad0df956c`.
Despite RAPT's filename, this is a disposable test fixture with a temporary
signing key and read-only observer; the build receipt marks `release: false`.

## Blockers resolved during continuation

The latest "Work" continuation adds Android text sharing for saved Records
and history. `services.share_text` opens the native text chooser; its callback
runs on Android's UI thread through the retained JNI helper without blocking
SDL. Synchronous failures raise `ShareError`, and asynchronous launch errors
queue a notification on Ren'Py's owning thread. The request has no send-result
claim. Exports contain only visible saved fields or plain dialogue, and never
submit or replace an unsaved Records draft.

The [first sharing run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38211152159)
passed the host suites but could not open the Android chooser. A
[diagnostic run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38212410093)
retained the native `JavaException`: `Intent.createChooser` had no overload
matching the Python string supplied for its Java `CharSequence` argument.
The backend now constructs/casts a Java string for that title. The callback
also uses positional arguments so Pyjnius's native `__cinit__(*args)` accepts
construction before the Python subclass initializer. Regression tests model
both JNI argument contracts alongside callback lifetime/error handling.

The [title-fix run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38213201543)
opened the chooser on the Android UI thread, but its text extra was a Java
`char[]`: Pyjnius selected that `putExtra` overload for a Python string.
The backend now passes explicit Java `String` objects for text and subject.
The [payload-fix run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38214007868)
then verified the exact Unicode/multiline history payload. Creating a saved
Record exposed an Android-only screen expression
using `input.Disable()` where `input` was Ren'Py's function. The screen now
uses the existing `DisableAllInputValues` action. A native regression evaluates
that same Android-only control, reproduced the exception before the fix, and
checks that sharing disables the keyboard while preserving the edited draft.
Full Android sharing acceptance is still pending after that correction.
Screenshot review also found that the resumed-activity dump could precede
the chooser's first frame, and the return check could read a pre-suspend
observer tick. The harness now waits for the real Android view hierarchy to
be idle, requires RenModPy to be the resumed activity on Back, and then
requires a newer same-process observer tick. CI disables system animations
and retains both view hierarchies and activity dumps with the screenshots.
Run `38215041919` was cancelled before Android acceptance because this
harness correction superseded it.

The APK observer inspects the identical Java Intent dispatched after a real
tap, records Android main-Looper affinity, and forwards the same request to
the platform. The harness opens and dismisses the chooser; it does not select
a receiving app. Prior verified lifecycle/clipboard receipts remain unchanged.

The later 2026-10-12 continuation focuses on Android background recovery.
The native lifecycle regression reproduced a pending `_reload-1` deletion:
a fresh process opened Home, skipped background saving because it was in the
main menu, then unconditionally deleted the previous process's recovery on
foreground return. This fell back to an older explicit Resume checkpoint.
`engine/patches/mobile-recovery-preservation.patch` keeps recovery under the
same main-menu/replay conditions that skip mobile saving. Normal foreground
return to the live story still removes its temporary checkpoint.

The [first lifecycle Android run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38198256469)
then exposed another real runtime failure while backgrounding Records with
the Android keyboard open. Logcat reported an OpenGL call with no current
context, followed by a shader error during renderer resize, before the SDL
suspend handler could write the recovery save. Its
[failure evidence](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38198256469/artifacts/11724856396)
contains the last draft state, screenshot and logcat.
`engine/patches/mobile-suspend-before-render.patch` handles queued and buffered
SDL suspend events before renderer resize/redraw using the existing native
save/wait/foreground handler. A new native real-event regression checks both
event paths and continued dialogue after foreground return.

The verified CI run passes both fixes on Android as well as the host checks.
Downloaded logcat records four native background entries, two live foreground
returns and five process starts (initial launch, two force-stop restarts and
two background process kills), with no engine traceback. The stopped-activity
dump confirms the example reached `STOPPED`; the committed receipt preserves
these observations and both resolved regression identities.

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
and ARM acceptance, Unicode IME composition, rotation/deep links and wider lifecycle profiles,
board touch/camera acceptance, other Android service operations, AAB packaging and
same-key updates remain unverified. Audio/video/ATL and richer app controls
still need representative native fixtures or implementation. The x86_64
emulator pass establishes the ten checks above, not full RenFletPy parity.

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
