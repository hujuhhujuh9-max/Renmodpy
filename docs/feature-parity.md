# RenFletPy feature benchmark

RenModPy's target is a continuous Android app whose Home, application screens,
dialogue and activities belong to one modified Ren'Py engine. Ren'Py/SDL owns
startup, rendering and Python. Built-in Python modules and common screens ship
inside that engine. New Android services can use Java/JNI or native code behind
the same Python API.

The behavioral benchmark is SDK-/RenFletPy at commit
`0fc79f001b2177a9a31dea31fd781b4cc298a510`, particularly its
[story/menu guide](https://github.com/hujuhhujuh9-max/SDK-/blob/0fc79f001b2177a9a31dea31fd781b4cc298a510/docs/renfletpy.md),
[reusable Records form](https://github.com/hujuhhujuh9-max/SDK-/blob/0fc79f001b2177a9a31dea31fd781b4cc298a510/docs/form-list.md)
and [capability assessment](https://github.com/hujuhhujuh9-max/SDK-/blob/0fc79f001b2177a9a31dea31fd781b4cc298a510/docs/flet-flutter-capabilities.md).

| User-facing capability | RenModPy implementation and evidence |
| --- | --- |
| Python, story syntax, characters, dialogue, choices | Modified Ren'Py 8.5.3; native dialogue/menu probe |
| Home, Return and durable Resume | Android menu round trip, first-dialogue cold Resume and latest background choice/dialogue recovery pass; cold Home app switches preserve recovery |
| Named checkpoints, dates, scene names and confirmations | Android name entry/create/confirmed overwrite/cold load/cancelled and confirmed delete pass; stale-selection guards remain host-tested |
| Quick save/load | Android restores the earlier dialogue/choice state after a later choice; newer Records and settings remain |
| Chronological story history | Android native history screen and saved chronology checked |
| Standard/larger text and animated/instant dialogue | Android larger/instant settings survive cold restart, older-save load and replay; headings remain readable |
| Replay | Android restart clears story/history/choice state; Records, preferences, quick and named saves remain |
| Record add/edit/cancel/delete/reload | Android add/edit/cancel/delete and saved/A–Z ordering pass; native probes and Python tests cover draft recovery, stale edits and failed writes |
| Custom fields and independent collections | `FormField`, `RecordDraft` and named private JSON collections; custom Android entry and collection isolation pass, alongside Python/native checks |
| Custom screens and activities | Ordinary Ren'Py screens, labels, Python and displayables; tactics demonstrates versioned custom save state |
| Clipboard copy/read and native form paste | Android history/record copy and Unicode/multiline Note paste pass; rejected Title paste keeps the draft; clipboard and pasted Records remain current after old-save load/replay |
| Plain-text sharing | Real Android choosers receive exact Unicode/multiline history and saved Records on the UI thread; Back keeps the draft/story/settings/saves and leaves input inactive; receiving-app delivery is unverified |
| Audio, video and ATL animation | Native Media room passes playback progression, decoded red/blue video frames, visible ATL motion and stop on menu replacement in both host renderers and Android; physical audibility unverified |
| Records ordering and richer app controls | Saved/A–Z Records ordering passes real Android interaction without changing stored rows or drafts. JSON editors, richer tables, color controls, cancellable loaders and charts need concrete use cases |
| File picker/attachment sharing, secure storage and haptics | Scoped import/export, cancellation, malformed backups and reviewed merges pass on Android; another UID reads the granted attachment. Keystore tamper/restart/old-load/replay/upgrade/delete and UI-thread haptics pass; physical feedback unverified |
| Deep links and lifecycle/device coverage | Android app switching, process kills and cold Home recovery pass; compact/tall/default sizes and densities keep the live draft and input in one interpreter, and a landscape request respects portrait orientation. Deep links and physical devices remain unverified |
| Project creation, release packaging and update acceptance | Fresh projects compile/lint/package; signed base/update APKs and a clean AAB pass. Installed same-key updates preserve Records, preferences, saves, story Resume and encrypted text; owner-key signing and physical devices remain |
| Rive/Lottie | Optional native integration when a concrete use case requires these formats |
| WebView | Out of scope by product choice |
| Phone camera, GPS and audio recording | Remain disabled |

The [verified run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38311573307) passes 81 Python tests,
33 checks with each real host renderer and 22 Android acceptance groups.
The APK targets API 36 and runs on Android 15/API 35 x86_64. Input coverage
includes a native composing InputConnection committing `café` and actual
custom form/Records interactions. Media evidence includes native playback
progression, six decoded video frames and visible ATL motion. Profiles cover
480×800/160 dpi, 1080×2400/320 dpi and 720×1280/160 dpi, with live state and
input retained; portrait orientation remains enforced after a landscape request.

The [services/media/packaging receipt](android-services-acceptance.json)
records all checks, source inputs, artifact hashes and expiry dates.
See [Codex handoff](codex-handoff.md) for current results. The earlier
[sharing](android-sharing-acceptance.json),
[lifecycle](android-lifecycle-acceptance.json),
[clipboard](android-clipboard-acceptance.json) and
[foundation](android-acceptance.json) receipts are retained unchanged.
Physical-device/ARM performance, hardware-backed Keystore behavior, audible
playback, felt haptics, other IMEs, deep links and board touch remain unverified.
Full RenFletPy parity has not yet been established.

Every follow-up feature should include its native implementation, integration
with the existing app/story session and the relevant save/lifecycle checks.
Use the existing Ren'Py implementation when it already provides the behavior.
