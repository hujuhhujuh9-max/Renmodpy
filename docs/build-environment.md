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
