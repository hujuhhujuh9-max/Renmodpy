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
| Record add/edit/cancel/delete/reload | Android keyboard entry/add/cold persistence pass; native host probes exercise editing/draft recovery, and Python tests cover stale/failed writes |
| Custom fields and independent collections | `FormField`, `RecordDraft` and named private JSON collections; Python tests and native multiline input probe |
| Custom screens and activities | Ordinary Ren'Py screens, labels, Python and displayables; tactics demonstrates versioned custom save state |
| Clipboard copy/read and native form paste | Android history/record copy and Unicode/multiline Note paste pass; rejected Title paste keeps the draft; clipboard and pasted Records remain current after old-save load/replay |
| Audio, video and ATL animation | Existing Ren'Py facilities remain; equivalent media/output fixtures have not been added to this fork |
| JSON editor, sortable tables, color controls, cancellable async loaders and charts | Reusable native equivalents still need implementation and representative interaction/output checks |
| Picker/sharing, secure storage, haptics and other Android services | Native engine APIs and device tests still needed for the donor's exercised operations |
| Deep links and lifecycle/device coverage | Android live Records draft/app switch, background process kill and cold Home recovery pass alongside force-stop/relaunch; deep links, rotation and wider device/lifecycle profiles remain pending |
| Project creation, release packaging and update acceptance | RAPT disposable APK and API 35 x86_64 interaction checks pass; physical-device, AAB, production signing and update acceptance remain pending |
| Rive/Lottie | Optional native integration when a concrete use case requires these formats |
| WebView | Out of scope by product choice |
| Phone camera, GPS and audio recording | Remain disabled |

The [verified run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38199188437)
passes 50 Python tests, 25 checks with each real host renderer and ten Android
emulator acceptance checks. The Android profile is API 35 x86_64 at 720×1280/160 dpi,
using an APK targeting API 36. It verifies the native app/story controls above,
including Unicode/multiline clipboard input, live app switching, two force-stop
restarts and two background process kills. Native recovery preserves the latest
waiting choice/dialogue, and app switching from cold Home keeps its pending
checkpoint. Broader JNI service operations, Unicode IME composition, board
touch, media output, physical-device performance and wider lifecycle/device
coverage remain unverified. See
[Codex handoff](codex-handoff.md) and the committed
[lifecycle acceptance receipt](android-lifecycle-acceptance.json). The earlier
[clipboard](android-clipboard-acceptance.json) and
[foundation](android-acceptance.json) receipts are retained. Full RenFletPy parity has not yet
been established.

Every follow-up feature should include its native implementation, integration
with the existing app/story session and the relevant save/lifecycle checks.
Use the existing Ren'Py implementation when it already provides the behavior.
