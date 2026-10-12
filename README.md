# RenModPy

One Android-only modified Ren'Py SDK, with app features integrated into its
Python runtime and native screens. Ren'Py/SDL owns rendering, story flow and
Android startup. This fork does not require Flet, Flutter or Dart.

## The vision

**RenModPy is "Ren'Py++" for Android: modified Ren'Py with a focused set of
useful additions.** Its space is Python stories, visual novels and integrated
Android app screens. RenFletPy is the quality benchmark for those features.
Reuse and adapt useful code and behavior from SDK- so it fits Ren'Py's Python
runtime and story workflow.

Godot already occupies the broader game-engine space. Building another full
general-purpose engine is outside this project's roadmap. Each RenModPy
addition should extend Ren'Py's story/Python workflow or connect a useful app
feature to that same experience.

Home, application screens, Records, settings, dialogue, choices and activities
should share one live session, one Python runtime, one project and one Android
APK. Moving between a story and an application screen should keep your place
in the story and feel like using the same application throughout.

The heart of the project is Ren'Py's Python runtime, story syntax, visual-novel
dialogue and character systems, and story-aware saves. Loading a story should
restore its position while keeping newer application Records and reading
settings. Tactics remains a secondary example; useful app controls and Android
capabilities should serve this continuous experience.

The creator's words capture the goal:

> It's just one thing, continuous thing

Progress toward this vision is recorded in [feature parity](docs/feature-parity.md).
Android quality must be demonstrated by running the APK on an Android emulator
or device and exercising real input, saves and restart behavior.

The user's [vision](docs/vision.md) and [original prompts](docs/user-prompts.md)
are preserved in the repository. See the [Codex handoff](docs/codex-handoff.md)
for current work, Android test status and continuation instructions.

## Current foundation

This first foundation reuses the modified Ren'Py 8.5.3 and RAPT inputs from
[`hujuhhujuh9-max/SDK-`](https://github.com/hujuhhujuh9-max/SDK-), pinned by
commit and archive SHA-256. Player rollback is already removed in the donor.
It adapts app records to a private file and supplies native Home, Records and
named-save screens. A ported tactics interlude exercises custom state saving.
The priority is preserving Ren'Py's Python and story workflow while adding
useful app screens.

## Assemble the SDK

Use Linux x86_64, Python 3.12+, Git, Git LFS and `patch`.

```bash
python3 -m unittest discover -s tests -t . -v
python3 build_sdk.py
.renmodpy-build/renmodpy-sdk/renpy.sh .renmodpy-build/renmodpy-sdk/renmodpy-example
```

Assembly installs engine additions into `renpy/renmodpy` and screens into
`renpy/common`, includes the example and RAPT, and writes a build receipt and
source notices. Output must be a fresh directory; pass `--output` for another
build. See [build environment](docs/build-environment.md) for offline inputs
and Android packaging.

## What is integrated

| Part | Native implementation |
| --- | --- |
| Home / Start / Return / Resume | Ren'Py menu contexts, a durable resume slot and latest Android background recovery |
| Records | Versioned JSON, atomic writes, stale-edit checks; outside story saves |
| Reusable record forms | Add/edit/cancel/delete/reload, multiline fields, custom schemas and collections |
| Clipboard | Copy visible record fields or plain history lines; append Unicode/multiline text to form drafts |
| Android text sharing | Native chooser for visible saved record fields and plain history lines; unsaved drafts are kept |
| Records backups and attachments | Scoped Android import/export, reviewed atomic merge and cache-backed attachment grants |
| Private text and touch feedback | Android Keystore AES-GCM outside backups; native UI-thread feedback requests |
| Audio, video and animation | Native Media room with playback controls, looping Movie and ATL motion |
| Fresh projects | SDK project creator with independent Android/save/build identity |
| Named checkpoints | Ren'Py save/load, confirmations and stale-save checks |
| Quick save/load, history, reading settings, replay | Native save slots, history/preferences and full engine restart |
| Tactics interlude | Saved board/camera state and a native displayable |
| Android JNI helpers | Donor class-loader setup, retained UI-thread callbacks and owner-thread worker results |

The example uses a 720×1280 portrait canvas. Screens are included in the
engine; projects choose which screens and story labels to use. The public
Python imports are `from renpy import renmodpy` and
`from renpy.renmodpy import services`.

Create a project from the assembled SDK:

```bash
python3 .renmodpy-build/renmodpy-sdk/create_project.py /path/to/my-story --name 'My Story' --package org.example.mystory
```

The creator refuses an existing destination and excludes keys, saves and test
observers. See [authoring](docs/authoring.md) for native Android services and
[packaging](docs/build-environment.md#fresh-projects-and-signed-artifacts) for
APK/AAB signing and updates.

## Verify the native runtime

```bash
python3 scripts/check_native.py --sdk .renmodpy-build/renmodpy-sdk
```

This compiles/lints a disposable copy of the example, renders its screens,
checks dialogue → Home → Resume, creates real Ren'Py saves, and restarts the
engine to check that board/story state restores while newer records remain.
It also creates an Android distribution and verifies that the added engine
modules and screens are included. It writes screenshots and a receipt under
`.renmodpy-build/native-check`. CI runs the same check.

The native checks also visit History/Settings/Records without advancing the
waiting dialogue, edit/reload multiline records, load a quick save after restart
and replay with fresh story state while keeping application data/preferences.

RenFletPy is the behavioral benchmark. See [feature parity](docs/feature-parity.md)
for implemented features and remaining Android-service/control gaps, and
[authoring](docs/authoring.md) for an integrated app/story project.

The [verified CI run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38311573307) passes 81 Python tests,
33 checks with each real native renderer and 22 Android acceptance groups on
Android 15/API 35 x86_64. Android tests exercise real composing Unicode input,
custom Records, clipboard/text choosers, scoped backup import/export, attachment
reads by another UID, private-storage tamper/restart/load/replay/delete,
native media output and a signed same-key installed upgrade. Records, current
settings, saves, story Resume and the encrypted entry survive the update.

The compact 480×800/160 dpi, tall 1080×2400/320 dpi and default 720×1280/160 dpi
profiles retain the live draft and tappable inputs in the same interpreter;
a landscape request respects the declared portrait orientation. Signed
base/update APKs and a clean-project AAB pass signature, version, permission,
ARM64/x86_64 packaging and downloaded-byte checks. The
[acceptance receipt](docs/android-services-acceptance.json) preserves source and
artifact hashes; the [Codex handoff](docs/codex-handoff.md) links the evidence.

Physical-device/ARM runtime checks, hardware-backed Keystore behavior, audible
playback, felt haptics, additional IMEs and deep links remain unverified.
Release signing requires the owner's retained key. Full RenFletPy parity is
still work ahead. Rive/Lottie and richer controls are optional additions when
a concrete use case needs them. WebView is out of scope. See the
[migration status](docs/migration.md) and [source provenance](docs/provenance.md).

The project retains the donor's ownership terms in [LICENSE](LICENSE).
Third-party notices stay with their components.
