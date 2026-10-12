# Build environment

The assembly host is Linux x86_64, matching the pinned donor SDK. The product
target is Android only. Host checks use Python 3.12 or later and the standard
library. Install Git LFS and `patch` for pinned input retrieval and the Android
activity-result patch. GitHub Actions also supplies SDL/Mesa and Xvfb for
native checks.

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

Successful runs write `.renmodpy-build/android-check/passed.json`. Screenshots,
last observed state, logcat and the emulator log are uploaded in the
`android-emulator-check` artifact, alongside the APK build log and checksum
receipt. A green Android job also uploads `android-validation-apk` with the
disposable APK and build receipt. These are validation artifacts, not an
application release. A failed or interrupted run must not retain `passed.json`.

The native check separately tests ordinary main-menu startup followed by cold
Home Resume/Quick load on the first dialogue. The local engine patch prevents
save restoration from crossing initialization; assembly records the patch's
hash and removes the stale compiled startup script. Android runtime acceptance
still requires the emulator job's actual interaction result. See
[Codex handoff](codex-handoff.md) for recorded runs and remaining device coverage.
