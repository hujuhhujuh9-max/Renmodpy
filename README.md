# RenModPy

One Android-only modified Ren'Py SDK, with app features integrated into its
Python runtime and native screens. Ren'Py/SDL owns rendering, story flow and
Android startup. This fork does not require Flet, Flutter or Dart.

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
| Home / Start / Return / Resume | Ren'Py menu contexts and a durable resume slot |
| Records | Versioned JSON, atomic writes, stale-edit checks; outside story saves |
| Named checkpoints | Ren'Py save/load, confirmations and stale-save checks |
| Tactics interlude | Saved board/camera state and a native displayable |
| Android JNI helpers | Donor class-loader setup; device validation pending |

The example uses a 720×1280 portrait canvas. Screens are included in the
engine; projects choose which screens and story labels to use. The public
Python imports are `from renpy import renmodpy` and
`from renpy.renmodpy import services`.

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

Android APK/AAB builds and physical-device input, keyboard and lifecycle tests
remain unverified in this foundation. Rive/Lottie and richer controls are
optional additions when a concrete use case needs them. WebView is out of
scope. See the
[migration status](docs/migration.md) and [source provenance](docs/provenance.md).

The project retains the donor's ownership terms in [LICENSE](LICENSE).
Third-party notices stay with their components.
