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
| Home, Return and durable Resume | Built-in screens and native bookmark; menu round trip and process restart checked |
| Named checkpoints, dates, scene names and confirmations | Native save browser; create/overwrite/delete, stale selection and restart/load checked |
| Quick save/load | Separate native slot; real save/restart/load checked |
| Chronological story history | Ren'Py history in a native screen; saved chronology checked |
| Standard/larger text and animated/instant dialogue | Native persistent preferences; restart and loading older saves keep newer settings |
| Replay | Full engine restart resets story variables/history; Records, preferences, quick and named saves remain |
| Record add/edit/cancel/delete/reload | Native reusable form; failed/stale writes keep the draft, invisible fields are preserved |
| Custom fields and independent collections | `FormField`, `RecordDraft` and named private JSON collections; Python tests and native multiline input probe |
| Custom screens and activities | Ordinary Ren'Py screens, labels, Python and displayables; tactics demonstrates versioned custom save state |
| Audio, video and ATL animation | Existing Ren'Py facilities remain; equivalent media/output fixtures have not been added to this fork |
| JSON editor, sortable tables, color controls, cancellable async loaders and charts | Reusable native equivalents still need implementation and representative interaction/output checks |
| Clipboard, picker/sharing, secure storage, haptics and other Android services | Native engine APIs and device tests still needed for the donor's exercised operations |
| Deep links and lifecycle/device coverage | RenModPy-specific acceptance pending |
| Project creation, release packaging and update acceptance | RAPT validation APK compiles; emulator startup blocked, app/device/update acceptance pending |
| Rive/Lottie | Optional native integration when a concrete use case requires these formats |
| WebView | Out of scope by product choice |
| Phone camera, GPS and audio recording | Remain disabled |

The implemented core is tested with the real modified engine on Linux and with
the launcher's Android distribution step. These checks do not establish Android
keyboard, touch, JNI, process-death recovery, media output or physical-device
performance. A validation APK now compiles, but the emulator action failed
before boot; see [Codex handoff](codex-handoff.md). Full RenFletPy parity has
not yet been established.

Every follow-up feature should include its native implementation, integration
with the existing app/story session and the relevant save/lifecycle checks.
Use the existing Ren'Py implementation when it already provides the behavior.
