# Codex handoff

## Verified Records-link milestone, 2026-10-14

Prompt 27 asks for repository-led continuation. The current remote branch was
unchanged from the completed services milestone. The concrete follow-up is
opening a saved default-collection Record from another Android entry point
without replacing a live form or loading/advancing a story.

The engine now captures initial/new Android VIEW Intents into one synchronized,
bounded pending text slot, consumed once on the Ren'Py owner. Projects opt in
with `renmodpy_deep_links`; the scheme comes from their own Android package.
Only canonical `package://records/<32-character lowercase hex ID>` links are
accepted. The Records screen offers Copy link. A modal read-only Title/Note
preview overlays the current interaction; closing keeps the draft and input
inactive. Missing Records show an unavailable message. Cold launch previews
over Home and leaves Resume explicit. Loading a checkpoint dismisses a preview
that was present in a mobile background save.

- Verified code/test revision: `5cb2aff0a9d6487d264b87db0ae001c4e65807ab`.
- [Green validation run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38581377270):
  88 Python tests, 36 checks in each native renderer and 27 Android acceptance groups.
- [Committed receipt](android-record-links-acceptance.json): all 34 source hashes,
  checks, caller/recovery evidence, signed binary/archive hashes and limitations.
- [Android evidence](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38581377270/artifacts/11904103058),
  [native evidence](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38581377270/artifacts/11904360871)
  and [signed APK/AAB fixtures](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38581377270/artifacts/11903863118)
  expire on 2026-10-28. Downloaded source inputs and artifact/binary bytes match.
- The [first Android run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38575199065)
  built signed APK/AAB artifacts and completed the earlier acceptance scope,
  then failed because Android Back did not close a repeated Record preview.
  The SDL `K_AC_BACK` key now explicitly closes this overlay; native validation
  injects both real SDL key events and checks the underlying form/history.
- Enabled projects now use `singleTask` so another app's flag-free VIEW Intent
  reuses the existing SDL activity. The new offline LinkActivity fixture sends
  that Intent from a real button tap in another UID; it has no network access.
- The [task-mode packaging run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38578128727)
  exposed the bundled Jinja 2.10 optimizer passing a null template name to
  RAPT's autoescape callback for an inline conditional expression. Use existing
  Jinja block syntax for the activity mode; the native check now renders both
  enabled and disabled manifests with the exact bundled version and preserves
  the resulting XML in its evidence.
- The [following emulator run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38578949993)
  passes Back and rejected-link cases and opens the preview from the external
  caller. It then stops at a harness-only UID-format assumption (`userId=` in
  `dumpsys package`). The observer now reports Android ApplicationInfo.uid,
  and the caller receipt is written before assertions for failure evidence.
- All five earlier acceptance receipts remain byte-for-byte unchanged.
- Authoring/API/scope: [Records links](authoring.md#links-to-saved-records).

The new Android cases pass after the existing 22 services/story/device groups.
A real offline caller tap sends an ACTION_VIEW Intent with no task flags;
caller UID 10210 differs from RenModPy UID 10209 and the same interpreter,
draft, story, Records and settings remain. Warm repeated links and Copy link
pass; Close/Android Back keep input inactive. Malformed/foreign/file/label and
non-VIEW Intents are ignored without changing data; missing Records stay
closable. Two new cold processes preview over Home. A background save made
with the preview visible survives process death byte-for-byte, and explicit
Resume restores the story without reopening the consumed overlay. Screenshots
were inspected. The disabled clean AAB omits the route/metadata; both rendered
manifest modes and the signed upgrade remain verified.

Custom collections/routes and verified HTTPS App Links remain outside this
initial implementation. Browser-specific behavior, disabled-project runtime,
physical ARM devices, other IMEs and production signing remain unverified.
Enabled single-task projects can close native activities above the app when
a link arrives. This section identifies the latest code and evidence.

## Completed continuation milestone, 2026-10-12

The remaining completion work authorized in prompt 24 is implemented and
verified on the emulator. RenModPy carries these additions inside one modified
Ren'Py/SDL engine: scoped Records backup import/export and reviewed atomic merge,
content-URI attachment sharing, Android Keystore AES-GCM private text, native
haptics, saved/A–Z Records ordering, a native audio/video/ATL Media room and SDK
project creation with independent Android/save/build identity.

- Verified code/test revision: `64edd698b80f34038700ce342420ea4730ff938f`.
- [Green CI run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38311573307):
  81 host tests, 33 checks in each real native renderer and 22 Android acceptance groups.
- [Committed acceptance receipt](android-services-acceptance.json): exact source
  inputs, checks, signing metadata, binary/archive hashes, artifact links and expiry.
- [Android evidence](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38311573307/artifacts/11775113203):
  screenshots, composing-IME receipt, decoded media frames, private-storage checks,
  document/receiver receipts, activity dumps and emulator/logcat output.
- [Signed validation artifacts](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38311573307/artifacts/11775397724):
  base APK, higher-version same-key APK and signed clean-project AAB. Downloaded
  bytes match the build receipt; private keys and test observers in the clean AAB
  are absent. These are disposable validation artifacts, not an app release.
- [Native evidence](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38311573307/artifacts/11774464380):
  both renderer receipts, fresh-process saves/restarts, media frames and SDK inventory.

Android acceptance runs on Android 15/API 35 x86_64 with an APK targeting API 36.
A real InputConnection composes/commits `café`. Custom collection forms, actual
Records add/edit/cancel/delete/sorting, clipboard/text choosers, scoped backup
cancel/export/import, malformed JSON rejection and confirmed merges pass while
keeping the draft. Another UID reads the granted attachment offline. Private
storage passes authenticated tamper rejection, cold restart, older-save loading,
replay, same-key upgrade and explicit delete/missing. Worker JNI uses the app
loader; callbacks run on the Ren'Py owner and haptics on Android's UI thread.

Native audio playback progresses, video decodes red/blue frames and ATL motion
is visible; stop/restart/menu replacement control the channels. The signed
installed upgrade preserves Records, custom collections, reading settings,
quick saves, story Resume and the exact encrypted entry. Signed APK/AAB metadata,
permissions, ARM64/x86_64 packaging and clean-project identity are verified.

Compact 480×800/160 dpi, tall 1080×2400/320 dpi and default 720×1280/160 dpi
profiles preserve the live draft, saved data and settings in the same interpreter,
with tappable inputs. A landscape request respects the declared portrait app.
The density manifest patch prevents Android from destroying the SDL activity.

The emulator also exposed a screen-local sorting lambda and cold first-dialogue
restoration after Replay. Sorting now binds its field explicitly. Replay captures
its target as plain story data before the save boundary; three fresh-process
regressions cover Resume/Quick load with a custom story label. Update builds
retain previous compiled statement identities. The harness measures the real
panned SDL view, settles native windows and avoids relaunching an already resumed
sender after sharing. Its screenshot check requires a visibly redrawn Records UI.

The offline document provider, receiver and composing IME belong only to the
validation APKs. Production projects remain ordinary Ren'Py projects. Work stays
on `bootstrap/native-foundation` in [draft PR #1](https://github.com/hujuhhujuh9-max/Renmodpy/pull/1).
No merge or application publishing has been requested. All four earlier receipts
below are retained unchanged. Physical ARM devices, hardware-backed Keystore
behavior, felt haptics, audible playback, other IMEs, deep links, board touch and
optional richer controls remain unverified. Full RenFletPy parity is not claimed.

## Earlier foundation and sharing milestone

RenModPy's native app/story foundation and text sharing pass Android emulator acceptance.
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
- Earlier verified engine/test revision: `9b83d78054685c30cf017c613c9b37cdc2578a4a`.
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

Native Android Share line/Share record actions export plain history or visible
saved fields with Unicode and line breaks intact. The chooser runs through the
retained UI-thread JNI callback; Back keeps the live menu, waiting story and
unsaved draft, with the form input inactive. Sharing does not submit Records,
change a save or report delivery to a receiving app.

The later lifecycle continuation preserves the newest native background
checkpoint when a freshly reopened Home is backgrounded before Resume. It
also handles queued/buffered SDL suspend events before renderer resize/redraw,
fixing the crash when switching apps with the keyboard open, discovered by the emulator.
Normal app switching retains the live Records draft and story session;
background process kills recover the waiting story choice or later dialogue.
Submitted Records and reading settings remain current.

The [completed CI run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38218211725)
passes all three jobs at the verified revision:

- 61 Python state/storage/form/build/clipboard/sharing/JNI callback tests.
- Real engine compile/lint, rendered menus, record editing, named saves,
  quick load, replay, Android distribution-input checks and the new ordinary
  startup/first-dialogue cold-load regression with both Linux renderers.
  Both renderers also pass SDL clipboard round trips and plain history export.
  Each passes 27 checks, including three-process choice/dialogue recovery,
  queued/buffered SDL suspend events before renderer redraw, unavailable-host
  sharing, and the Android-only Records control across input interactions.
- RAPT APK compilation and real Android interaction on a rooted Android 15 /
  API 35 x86_64 emulator, at 720×1280 and 160 dpi.

The Android harness drives ADB taps and keyboard events; its APK observer only
reports state and observes the identical native sharing Intent. The eleven
completed acceptance checks cover:

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
11. History/Records taps opening real text choosers with exact Unicode/multiline
    payloads on Android's main Looper. Back resumes the same process/menu, keeps
    the draft/story/Records/settings/saves, leaves Records input inactive and
    releases the JNI callback. No receiving app is selected.

The lifecycle screenshots show the retained Records draft and recovered
choice/dialogue. Records screenshots also show the pasted accented, multiline
lighthouse note and the copied saved record. The earlier foundation run captured the
Android software keyboard during entry.
Menu headings now fit their reserved width, including with larger text, and
the save-name field can be deselected to close the keyboard.

## Evidence and validation APK

The latest receipts, APK checksum and engine/example input hashes are
preserved in [android-sharing-acceptance.json](android-sharing-acceptance.json).
The earlier [lifecycle](android-lifecycle-acceptance.json), [clipboard](android-clipboard-acceptance.json) and
[foundation](android-acceptance.json) receipts remain unchanged. Downloaded CI
input hashes were compared with the review code and match. Later documentation
updates do not change those engine/example inputs.

- [Android job and log](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38218211725/job/114707847436)
- [Android state, chooser/return screenshots, native Intents, view hierarchies, activity dumps, logcat and build receipt](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38218211725/artifacts/11733786529)
- [Disposable validation APK and checksum receipt](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38218211725/artifacts/11733216793)
- [Both native renderer receipts and screenshots](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38218211725/artifacts/11733760948)

The artifact retention period is 14 days, expiring on 2026-10-26. The committed
receipt remains available after the downloadable artifacts expire.

The APK is `org.renmodpy.example-0.1.0-1791790345-release.apk`, targeting API 36.
Its SHA-256 is
`2e4c4ee454a41a554dc8061320ba25ffcd2f4b99bd6adce7e4ff69cf0d51078c`.
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
these JNI argument contracts alongside callback lifetime/error handling.

The [title-fix run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38213201543)
opened the chooser on the Android UI thread, but its text extra was a Java
`char[]`: Pyjnius selected that `putExtra` overload for a Python string.
The backend now passes explicit Java `String` objects for text and subject.
The [payload-fix run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38214007868)
then verified the exact Unicode/multiline history payload. Creating a saved
Record exposed an Android-only screen expression
using `input.Disable()` where `input` was Ren'Py's function. The screen now
disables the actual form input values. A native regression evaluates that same
Android-only control and reproduced the exception before the fix. It also
checks the next interaction, when Ren'Py's `DisableAllInputValues` would
otherwise reactivate the default field. Disabling each value preserves the
inactive input and edited draft across that interaction.
Screenshot review also found that the resumed-activity dump could precede
the chooser's first frame, and the return check could read a pre-suspend
observer tick. The harness now waits for the real Android view hierarchy to
be idle, requires RenModPy to be the resumed activity on Back, and then
requires a newer same-process observer tick. CI disables system animations
and retains both view hierarchies and activity dumps with the screenshots.
Run `38215041919` was cancelled before Android acceptance because this
harness correction superseded it.
The [following run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38215361349)
passed all 61 Python, 27 checks per native renderer and 11 Android checks.
Its screenshots confirmed both real text choosers and draft retention, but
also exposed the default-input refocus on return to Records. The new native
next-interaction assertion fails on that revision; Android acceptance now
also requires the returned Records input to stay inactive. The final run
validates the focus correction.
The [focus-fix run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38216516268)
passed both native renderer suites, but stopped at History's UI capture:
UIAutomator returned without creating its XML file. The retained screenshot
and Intent show the real chooser was already open with the correct text.
The harness now retries capture within a 60-second deadline, records each
command's output, and requires valid XML from the expected foreground package.
The same-process return and inactive-input assertions remain required.
The [capture-retry run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38217325359)
passed History sharing, view capture and foreground return, then exposed a
redundant form-focus tap in the harness before typing the retained draft.
The generic observer tick could precede the first toggle; a second tap then
disabled the field. Draft setup now focuses once, scrolls if needed, and waits
for the specific editable field before typing.

The final run at `9b83d78054685c30cf017c613c9b37cdc2578a4a` passes all
61 Python tests, 27 checks per native renderer and 11 Android checks. Downloaded
Intent reports, chooser/return screenshots and source hashes match the review
code. The returned Records screenshot visibly retains “Keep draft” with the
keyboard closed. History capture needed one retry; the retained diagnostics
confirm the expected Android hierarchy became ready on the second attempt.
The APK checksum was independently verified against the downloaded binary.

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

Use the verified Records-link milestone at the top and [feature-parity.md](feature-parity.md).
Preserve all six receipts and their source identities. Continue with physical
ARM-device input, hardware-backed Keystore, felt haptics and audible media in
the owner's environment, then other IMEs, browser-specific link delivery,
disabled-project runtime, board touch or richer controls when a concrete use
case calls for them. Custom routes and verified HTTPS App Links need their own
use case and acceptance. Production releases require the owner's retained signing key and
previous compiled scripts for save compatibility. Full RenFletPy parity is not
established by one emulator and three display profiles.

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
