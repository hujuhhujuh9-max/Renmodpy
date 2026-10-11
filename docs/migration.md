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
| Home and story Start/Return/Resume | Native example |
| Records independent of story checkpoints | Atomic private file and native screen |
| Named story saves and confirmations | Native backend and screen |
| Quick save/load, history, reading preferences and replay | Native screens and engine APIs |
| Record edit/cancel/reload, multiline/custom fields and collections | Built-in reusable form and draft recovery |
| Android JNI worker class-loader helpers | Imported; phone verification pending |
| Flutter/Flet controls and transport | Not included |
| WebView | Out of scope |
| Rive/Lottie animations | Optional; a concrete use case is needed |
| Secure storage and picker | Follow-up only when needed |
| Rich code editor and advanced tables | Optional feature-specific work |

The example uses native Ren'Py menu contexts to retain live story progress.
Returning home also writes a durable resume bookmark. Android recovery slots
are eligible for Resume after a restart. Completion clears resume/recovery
bookmarks; named manual checkpoints remain available.

New records are stored outside Ren'Py's saved store. Loading a story restores
its script position and board state while reading the current record file.
Old SDK- preferences records and story bookmarks are not automatically migrated;
their storage/key names and saved module identities differ.

The Android 15/API 35 x86_64 emulator now verifies keyboard entry, Home/Resume,
named saves, cold process restart, older Quick load, Records/preferences
preservation and replay. A local engine patch fixes first-dialogue saves
restoring across startup initialization. The acceptance receipt and source
identity are recorded in [Codex handoff](codex-handoff.md).

Physical-device/ARM, Unicode Android input, rotation/background recovery,
board touch/rendering, Android services and AAB/update acceptance remain
pending. Import checks and Linux probes do not establish these device results.

See [feature parity](feature-parity.md) for the RenFletPy benchmark, current
evidence and remaining gaps, and [authoring](authoring.md) for one app/story
project and reusable native Records forms.
