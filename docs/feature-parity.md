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
| Home, Return and durable Resume | Android menu round trip and first-dialogue cold Resume pass; startup save-boundary regression also passes with both host renderers |
| Named checkpoints, dates, scene names and confirmations | Android name entry/create/confirmed overwrite/cold load/cancelled and confirmed delete pass; stale-selection guards remain host-tested |
| Quick save/load | Android restores the earlier dialogue/choice state after a later choice; newer Records and settings remain |
| Chronological story history | Android native history screen and saved chronology checked |
| Standard/larger text and animated/instant dialogue | Android larger/instant settings survive cold restart, older-save load and replay; headings remain readable |
| Replay | Android restart clears story/history/choice state; Records, preferences, quick and named saves remain |
| Record add/edit/cancel/delete/reload | Android keyboard entry/add/cold persistence pass; native host probes exercise editing/draft recovery, and Python tests cover stale/failed writes |
| Custom fields and independent collections | `FormField`, `RecordDraft` and named private JSON collections; Python tests and native multiline input probe |
| Custom screens and activities | Ordinary Ren'Py screens, labels, Python and displayables; tactics demonstrates versioned custom save state |
| Audio, video and ATL animation | Existing Ren'Py facilities remain; equivalent media/output fixtures have not been added to this fork |
| JSON editor, sortable tables, color controls, cancellable async loaders and charts | Reusable native equivalents still need implementation and representative interaction/output checks |
| Clipboard, picker/sharing, secure storage, haptics and other Android services | Native engine APIs and device tests still needed for the donor's exercised operations |
| Deep links and lifecycle/device coverage | Android force-stop/relaunch and explicit Resume/named load pass; deep links, rotation and broader background recovery remain pending |
| Project creation, release packaging and update acceptance | RAPT disposable APK and API 35 x86_64 interaction checks pass; physical-device, AAB, production signing and update acceptance remain pending |
| Rive/Lottie | Optional native integration when a concrete use case requires these formats |
| WebView | Out of scope by product choice |
| Phone camera, GPS and audio recording | Remain disabled |

The [verified run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38178146432)
passes 42 Python tests, both real host renderers and six Android emulator
acceptance checks. The Android profile is API 35 x86_64 at 720×1280/160 dpi,
using an APK targeting API 36. It verifies the native app/story controls above,
including visible software-keyboard entry and two process restarts. JNI service
operations, Unicode Android input, board touch, media output, physical-device
performance and wider lifecycle/device coverage remain unverified. See
[Codex handoff](codex-handoff.md) and the committed
[acceptance receipt](android-acceptance.json). Full RenFletPy parity has not yet
been established.

Every follow-up feature should include its native implementation, integration
with the existing app/story session and the relevant save/lifecycle checks.
Use the existing Ren'Py implementation when it already provides the behavior.
