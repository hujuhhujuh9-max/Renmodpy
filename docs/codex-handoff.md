# Codex handoff

Read [vision.md](vision.md), [user-prompts.md](user-prompts.md) and `AGENTS.md`
first. The intended result is one continuous Android-only modified Ren'Py
application with RenFletPy as the quality benchmark.

The user clarified the niche as "Ren'Py++": modified Ren'Py with focused
additions for Python stories, visual novels and integrated Android app screens.
Godot's broader general-purpose engine scope remains outside the roadmap.
Apply later user corrections when interpreting voice-transcription errors.

## Where the work is

- Repository: `hujuhhujuh9-max/Renmodpy`.
- Review branch: `bootstrap/native-foundation`.
- Draft review: [PR #1](https://github.com/hujuhhujuh9-max/Renmodpy/pull/1).
- Current engine/test code: `34116ba0dc892f231bf631e99729e4f3d45bf474`.
- Donor benchmark: SDK- `0fc79f001b2177a9a31dea31fd781b4cc298a510`.
- Ren'Py/RAPT inputs are pinned in `sdk-lock.json`; provenance is retained.

The user has not requested a merge or an application release. Keep changes
reviewable. Their latest instruction is to stop on another environment blocker
and leave this handoff for Codex to continue in a better environment.

## Implemented

The assembled SDK contains native Home/Return/Resume, named checkpoints,
quick saves, history, persistent reading settings, full story replay and
editable Records. Record forms support custom fields, independent collections,
multiline input, stale-edit protection and preserving a draft on failed writes.
Application Records remain independent of story snapshots. The example now
explicitly opens Home through its `main_menu` label.

The tactics example is a regression fixture for versioned activity state,
rendering and save/load. It is not the main product. Rich controls and Android
services are still incomplete; use [feature-parity.md](feature-parity.md), not
an assumption of full RenFletPy parity.

## Verification and current Android attempt

41 Python state/storage/form/build tests pass. Clean CI also passes real native
engine compile/lint, menu continuity, records editing, save/delete/load,
quick-load, full replay and Android distribution-input checks with both Linux
renderers. These checks do not establish Android runtime acceptance.

The managed local workspace intermittently showed a deleted save file returning
after a native subprocess. The exact deletion/replay assertions passed in clean
CI with both renderers. The local discrepancy's cause was not isolated; no
speculative engine filesystem patch was retained.

The workspace has no `adb`, `emulator` or `sdkmanager`. An Android CI job was
added instead. Its first attempt failed because the runner lacked SDK tools;
explicit `android-actions/setup-android` installation was then added.

The next attempt installed the Android SDK and **successfully built the APK**
through RAPT. The validation output was
`org.renmodpy.example-0.1.0-1791754327-release.apk`, signed with the disposable
test key. The emulator action then failed before launching the emulator:

```text
Error: Cannot find module '@actions/core'
.../ReactiveCircus/android-emulator-runner/ed009f5318f15b1cf93a191b856c4f1748a2d4c1/lib/main.js
code: 'MODULE_NOT_FOUND'
```

**Stopped at this blocker, as the user requested.** No emulator boot,
installation into an emulator, Android app launch, input test or restart test
completed. The Android observer and ADB harness remain unvalidated on Android.
Do not treat APK compilation as an emulator pass. Do not retry this action
indefinitely in the current environment.

Evidence and exact source revision:

- [Android test run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38176677164)
- [Android APK/emulator job](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38176677164/job/114580424248)
- [Parallel push run](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38176673405)
- [Build log and receipt artifact](https://github.com/hujuhhujuh9-max/Renmodpy/actions/runs/38176677164/artifacts/11715594829)

`scripts/build_android_check.py` builds a disposable validation APK using the
ordinary RAPT path and a temporary test signing key. `scripts/android_probe.rpy`
is a read-only observer copied into that test project. It does not call app
actions. `scripts/check_android.py` drives actual ADB taps and text events, then
checks force-stop/relaunch, durable Resume and loading an older quick save
without rewinding newer Records or reading preferences.

The configured emulator is Android 15/API 35, x86_64, with a Nexus 5 profile.
The APK targets API 36. This one emulator cannot establish physical-device,
ARM, performance or complete Android-service acceptance. The validation APK
contains the observer and uses a disposable key; it is not a release build.

The `android-emulator-check` artifact from this attempt contains only the build
log and build receipt. No emulator screenshots, state, logcat or `passed.json`
were produced. Future successful runs should upload those files; `passed.json`
is written only if all emulator assertions finish. A green host/native job does
not replace a green Android job or this Android receipt.

## Continue in an Android-capable environment

Use Linux x86_64 and Python 3.12+ for SDK assembly, JDK 21, Android SDK platform
36/build-tools 36, `adb` and a working Android emulator. Read
[build-environment.md](build-environment.md) for pinned/offline build inputs.

```bash
python3 -m unittest discover -s tests -t . -v
python3 build_sdk.py
python3 scripts/build_android_check.py --sdk .renmodpy-build/renmodpy-sdk
# With the rooted validation emulator running:
python3 scripts/check_android.py
```

`ANDROID_HOME` must point to the installed SDK. Assembly needs a fresh output
directory. The ADB harness expects the rooted CI emulator, not a user's phone.
If Android fails, inspect the build log, logcat, state and screenshots before
changing engine code. Respect the user's stop instruction in the current
environment; use the handoff rather than repeatedly adding workarounds.
