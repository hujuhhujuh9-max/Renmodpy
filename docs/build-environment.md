# Build environment

The assembly host is Linux x86_64, matching the pinned donor SDK. The product
target is Android only. Host checks use Python 3.12 or later and the standard
library. Install Git LFS and `patch` for pinned input retrieval and the Android
activity-result patch. GitHub Actions also supplies SDL/Mesa and Xvfb for
native checks. Screenshot evidence checks additionally use Pillow 12.3.0;
install it with `python3 -m pip install Pillow==12.3.0` before native validation.

`python3 prepare.py setup` downloads only Ren'Py and RAPT from their pinned
component commits. Size and SHA-256 checks run before extraction. No Flutter,
Flet extension or hybrid Android host is fetched. The lock file records all
component and patch identities.

For an offline build, put the two exact locked archive filenames in a
directory and use:

```bash
python3 build_sdk.py --archives /path/to/archives --output /path/to/fresh-sdk
```

The Android patch and third-party notices still require the pinned Git source
objects in the build cache. Run preparation/assembly online once to populate
that cache before going offline. `--cache-dir` chooses its location.

For host-only validation, `--host-check-only` omits RAPT. It does not produce
an Android application. The assembled SDK's `renpy.sh` can run its native
example directly on the validation host.

## Android packaging

Use the assembled RenModPy launcher's Android workflow for
`renmodpy-example`. RAPT supplies its normal Android SDK/JDK installation,
configuration, key generation and APK/AAB packaging flow. Java/build tools
may need additional downloads; the locked RAPT archive alone is not a full
offline Android toolchain.

The example's `.android.json` uses `org.renmodpy.example`, portrait orientation
and no requested optional permissions. Change the package before distribution.
Do not commit generated signing keys. No APK/AAB or signed release is produced
by the current native check.

The native check runs the launcher's Android distribution step and checks the
compiled engine modules, common screens, example script and Android settings.
This verifies packaging inputs without installing Google's Android toolchain.
It does not compile an APK or execute the app on Android.

Before accepting Android support, build and install on a device and verify:

- Records input with the Android keyboard, including Unicode and rotation/backgrounding.
- Start, Home, Return, Resume after process death, and completion clearing Resume.
- Named save/load/overwrite/delete, including the tactics camera and unit positions.
- New records remaining after loading older story checkpoints.
- Tap, pan, zoom and camera controls on the board; no camera/location/recording permissions.

The engine includes its own added Python package in the normal Ren'Py tree.
There is no separate app server or second Python interpreter to launch.

## Android emulator validation

The Android CI job installs JDK 21, Android SDK platform 36/build-tools 36,
`adb`, the emulator and the Android 15/API 35 `google_apis` x86_64 image. It
creates an isolated Pixel 2 AVD, starts it directly with KVM and SwiftShader,
and waits for Android to finish booting. This follows SDK-'s working emulator
setup and avoids the failed emulator action. Pull-request updates run one
validation workflow; the additional branch push run has been removed.

With that toolchain installed and `ANDROID_HOME` set:

```bash
python3 build_sdk.py --output .renmodpy-build/android-sdk
python3 scripts/build_android_check.py --sdk .renmodpy-build/android-sdk
python3 scripts/build_android_fixtures.py
# Start a disposable rooted Android emulator before this command:
python3 scripts/check_android.py
```

The harness clears `org.renmodpy.example` data. It requires an emulator and
root before installation/data clearing, so it is unsuitable for a user's
phone. The APK targets API 36 and uses a temporary test signing key; it contains
a read-only observer that never calls app actions. The harness drives ADB taps
and keyboard events through the built-in screens. It tests the first dialogue's
cold Resume, restoration of an older quick save after making a story choice,
named save/overwrite/load/delete confirmations and replay. Application Records
and current reading preferences must survive story restoration and replay.
Native history/record copy and Unicode/multiline form paste also run through
real taps. Rejected Title paste must retain the draft, and pasted Records and
the current platform clipboard must survive older-save loading and replay.
The read-only observer exports clipboard text only inside this disposable
validation APK; production screens read it only on a requested Paste action.

Lifecycle checks press Android's system Home, wait for the activity to stop and
for its native recovery file to be written, then return through the real
activity. The live Records draft must remain unchanged without creating a
record. Separate checks kill the stopped app process with `am kill`, reopen
Home and use Resume to recover a waiting choice and later dialogue newer than
the explicit saves. Switching apps again from cold Home must keep that pending
recovery file byte-for-byte. Observer boot IDs distinguish the live return from
the new processes; a paused observer is never used to drive recovery.

Successful runs write `.renmodpy-build/android-check/passed.json`. Screenshots,
last observed state, logcat and the emulator log are uploaded in the
`android-emulator-check` artifact, alongside the APK build log and checksum
receipt. The Android job also uploads `android-validation-apk` with the
signed base/update APKs, clean-project AAB and build receipt, including when
an interaction check fails after successful packaging. These are validation
artifacts, not an application release. A failed or interrupted run must not retain `passed.json`.

The native check separately tests ordinary main-menu startup followed by cold
Home Resume/Quick load on the first dialogue. The local engine patch prevents
save restoration from crossing initialization; assembly records the patch's
hash and removes the stale compiled startup script. Android runtime acceptance
still requires the emulator job's actual interaction result. See
[Codex handoff](codex-handoff.md) for recorded runs and remaining device coverage.

The native lifecycle probe also uses three fresh processes to exercise the
engine's real mobile-save/cleanup methods and load the recovery through Home.
It verifies that cold Home preserves a pending checkpoint, that a waiting
choice and later dialogue restore, and that returning to the live story still
clears the temporary save. The recovery-cleanup patch is recorded in the SDK
input inventory. This host policy check complements the Android OS interaction
checks above.

Sharing checks tap History's Share line and Records' Share record, then wait
for Android's actual chooser activity. The validation observer inspects the
identical Java Intent passed to `startActivity`, recording its chooser/send
actions, `text/plain` MIME type, Unicode/multiline text, absent attachment and
Android main-Looper affinity. It observes a request from a real tap and forwards
the same Intent through the ordinary launcher; it never selects a receiving app.
Android Back dismisses the chooser. The harness requires the same process,
draft, waiting story, Records, reading settings and saves on return, and verifies
that the retained JNI callback has been released. Chooser/return screenshots,
activity dumps, Android view hierarchies and Intent JSON are included in the
Android evidence artifact. The harness waits for the Android view hierarchy to
be idle before capture; Back must resume RenModPy's activity and produce a
newer same-process observer tick. System animations are disabled on the
disposable emulator to keep captures stable.
Receiving-app delivery is outside this text-sharing check. The new document and
attachment check uses a separate offline fixture app, described below.

## Fresh projects and signed artifacts

The assembled SDK includes a project creator:

```bash
python3 /path/to/sdk/create_project.py /path/to/my-story --name 'My Story' --package org.example.mystory
/path/to/sdk/renpy.sh /path/to/my-story compile
/path/to/sdk/renpy.sh /path/to/my-story lint
```

It refuses existing destinations, assigns the project's own Android/save/build
identity and copies the ordinary example without saves, keys or test observers.
Edit `game/script.rpy` and the project's `.android.json` for your application.
The example's portrait orientation and empty optional permission list are the
starting configuration.

For a distributable application, use RAPT's normal key-generation/configuration
workflow or your existing signing configuration. Keep and back up the same
signing key for future updates. Stock RAPT project keys are `android.keystore`
and `bundle.keystore` with alias/password `android`; an existing custom signing
configuration can use `update_keystores: false` and the SDK's
`rapt/project/local.properties`/`bundle.properties`. These files hold signing
credentials and must remain private. Configure the installed Android SDK path
in `rapt/sdk.txt`, then build through the same native launcher:

```bash
/path/to/sdk/renpy.sh /path/to/sdk/launcher android_build /path/to/my-story --destination /path/to/artifacts/apk
/path/to/sdk/renpy.sh /path/to/sdk/launcher android_build /path/to/my-story --bundle --destination /path/to/artifacts/aab
```

Increment `version` and `numeric_version` in `.android.json` for an update and
keep `config.version` consistent. RAPT also ensures its numeric version is at
least the build timestamp. Retain the previous release's `.rpyc` files alongside
the source, or copy them into an `old-game` directory beside `game`, before
recompiling an update. Ren'Py uses them to match statement identities so older
story saves can find their original position. Back them up with each release,
including when Git ignores compiled files. Verify APK signatures with
`apksigner verify --print-certs` and AAB signatures with `jarsigner -verify`; then exercise an APK
update using `adb install -r` without clearing data. Creating these artifacts
does not publish an app or upload anything to a store.

CI now creates its validation project through the same creator, builds a base
APK and a higher-version APK with the same disposable signing key, and builds
a signed AAB from a separate clean project. It verifies matching public signing
certificate digests and ARM64/x86_64 bundle libraries. Keystores are excluded
from artifacts and source control. These disposable keys are unsuitable for a
production app; owner-key signing and physical-device installation need the
owner's actual release environment.

The second fixture APK supplies a local DocumentsProvider, offline attachment
receiver with a different UID and an InputConnection composing keyboard.
System picker taps select/read/write real content URIs; the receiver reads only
the granted attachment and writes its local receipt. It sends no messages and
has no network permission. The keyboard commits composed Unicode through the
actual native input connection. Private-storage checks inspect encryption,
reject tampering and verify persistence across loads/restarts/upgrades. Media
checks compare decoded video colors and ATL positions in screenshots and
observe native playback progression. The latest emulator run passes all 27
acceptance groups, including live
480×800/160 dpi, 1080×2400/320 dpi and 720×1280/160 dpi profiles and declared
portrait orientation. Density is handled by the SDL activity, preserving its
interpreter and draft. See [acceptance evidence](android-record-links-acceptance.json).
Headless playback does not establish audibility or felt haptics.

The native screen probe also evaluates the Android-only Records Share button
using a screen-local platform flag. It runs the actual input-dismissal action
and host failure path, verifying that the edited draft and stale-edit status
are retained. This checks screen expressions without substituting for the
emulator's JNI, chooser and lifecycle acceptance.

## Record-link validation

The example enables `renmodpy_deep_links` in its Android configuration. Enabled
projects use their package-specific scheme and a single-task SDL activity;
disabled projects retain single-top mode and omit the link filter/metadata.
The native check renders both modes using RAPT's bundled Jinja 2.10, including
underscore-to-`+` scheme conversion, and retains the XML in its evidence.
The clean-project AAB disables links and its compiled manifest is checked.

Android acceptance delivers implicit VIEW Intents to the packaged route, then
explicit malformed/file/foreign/label/non-VIEW requests to the native boundary.
It tests repeated delivery, actual Copy link, Close/Android Back and missing
Records while preserving the live form and waiting story. The separate offline
LinkActivity fixture also launches a VIEW Intent with no task flags from a
real native button tap; ApplicationInfo.uid and the fixture receipt establish
different UIDs, while observer boot IDs establish the same interpreter.

Cold link launches preview over Home and leave Resume explicit. A background
checkpoint made with the overlay visible must remain byte-for-byte unchanged
after process death/link launch, restore the waiting story on Resume and keep
the consumed preview dismissed. These five groups extend the earlier 22
services/story/device groups. Browser-specific delivery, verified HTTPS App
Links and disabled-project runtime are outside this check; see
[authoring](authoring.md#links-to-saved-records) and the
[acceptance receipt](android-record-links-acceptance.json).
