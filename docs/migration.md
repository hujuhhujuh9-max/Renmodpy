# Migration status

The product target is Android. Linux is used to assemble the SDK and verify
native Ren'Py behavior, not as an additional supported product platform.

The first priority is preserving Python, story syntax, dialogue and story-aware
saves, then integrating useful app screens. The tactics interlude is retained
as a custom-state save test. It is not the main product direction.

| Capability | First foundation |
| --- | --- |
| Modified Ren'Py with rollback removed | Pinned donor archive |
| One Ren'Py/SDL host and Python interpreter | Preserved |
| Tactics movement, camera and native rendering | Imported and adapted |
| Home and story Start/Return/Resume | Native menus and latest Android background recovery |
| Records independent of story checkpoints | Atomic private file and native screen |
| Named story saves and confirmations | Native backend and screen |
| Quick save/load, history, reading preferences and replay | Native screens and engine APIs |
| Record edit/cancel/reload, multiline/custom fields and collections | Built-in reusable form and draft recovery |
| Clipboard copy/read and Unicode form paste | Native SDL services, Records and history actions; Android acceptance passes |
| Android text sharing | Native text chooser through the engine API, Records and history actions; exact Unicode/multiline payload and draft-preserving return pass on Android |
| Android JNI class-loader helpers | Imported worker helper plus retained UI-thread sharing callbacks; phone/worker coverage pending |
| Flutter/Flet controls and transport | Not included |
| WebView | Out of scope |
| Rive/Lottie animations | Optional; a concrete use case is needed |
| Secure storage and picker | New native Keystore/scoped-document APIs and Records backups; Android validation in progress |
| Rich code editor and advanced tables | Optional feature-specific work |

The example uses native Ren'Py menu contexts to retain live story progress.
Returning home also writes a durable resume bookmark. Android recovery slots
are eligible for Resume after a restart. Completion clears resume/recovery
bookmarks; named manual checkpoints remain available.
Cold Home preserves a pending recovery when the user switches apps before
pressing Resume. Normal foreground return to a live story keeps its session
and clears its temporary background save. Records drafts survive that live
app switch; submitted Records remain independent of story recovery.

New records are stored outside Ren'Py's saved store. Loading a story restores
its script position and board state while reading the current record file.
Old SDK- preferences records and story bookmarks are not automatically migrated;
their storage/key names and saved module identities differ.

The Android 15/API 35 x86_64 emulator now verifies keyboard entry, Home/Resume,
named saves, cold process restart, older Quick load, Records/preferences
preservation and replay. Native clipboard copy and Unicode/multiline field paste
also pass, including rejected-paste draft retention. Lifecycle acceptance now
passes live Records draft retention, recovery of a waiting choice and later
dialogue after background process kills, and cold Home app switching.
Native History/Records sharing now passes exact text payload, Android UI-thread
dispatch and same-process chooser return checks. The unsaved draft remains
intact and the form input stays inactive on return. The native callback is
released and is never part of a story save.
Local engine patches fix first-dialogue saves restoring across initialization,
pending-recovery cleanup and SDL suspension running after renderer resize.
The acceptance receipt and source
identity are recorded in [Codex handoff](codex-handoff.md).

Physical-device/ARM, Unicode IME composition, rotation/deep links and wider lifecycle profiles,
board touch/rendering, file picking/attachment sharing, receiving-app delivery,
other Android services and AAB/update acceptance remain
pending. Import checks and Linux probes do not establish these device results.

See [feature parity](feature-parity.md) for the RenFletPy benchmark, current
evidence and remaining gaps, and [authoring](authoring.md) for one app/story
project and reusable native Records forms.
