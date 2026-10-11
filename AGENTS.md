# Working on RenModPy

Read `docs/vision.md`, `docs/user-prompts.md` and `docs/codex-handoff.md` before
continuing. Preserve the user's original prompts and update the handoff with
actual results. The user expects Android emulator testing; Linux tests and
distribution inputs alone do not establish Android runtime acceptance. The
earlier session stopped at an emulator-action blocker and handed off to Codex;
the user has now authorized continuation. If a new installation/testing
environment blocker prevents acceptance, preserve its evidence in the handoff.

The product is one Android-only modified Ren'Py SDK. Ren'Py/SDL owns startup,
rendering, story flow, and the Python interpreter. Features imported from SDK-
must be integrated into RenModPy; do not reintroduce Flet, Flutter, Dart, or a
second Python startup owner.

Use RenFletPy's working user-facing behavior as the quality benchmark. Home,
app screens and stories must share one live session in the modified engine.
Track missing capabilities honestly in `docs/feature-parity.md`; integration
alone is not feature parity. Add required native implementations behind the
engine's Python API, and keep Android/device acceptance separate from host tests.

Prioritize Python/story syntax, dialogue, story-aware saves and useful app
screens. Tactics is a regression example, not the main product. WebView is
out of scope. Rive/Lottie and complex controls require a concrete use case
before adding their runtimes.

Engine Python additions live in `engine/python/renmodpy`. SDK assembly installs
them into `renpy/renmodpy`; built-in screens live in `engine/common` and are
installed into `renpy/common`. These are part of the assembled engine and
ordinary Android packaging, not an external application service.

Use existing Ren'Py APIs when they implement the required behavior. Change
engine internals or Android host code for a demonstrated missing capability.
Android/Java/Kotlin/C++ implementations may sit behind the built-in Python API.
Keep original source notices and record every donor commit in provenance.

Application data must remain independent of story saves. Save only plain,
versioned activity data; exclude render caches, locks, listeners and native
services. Run flow/save operations on Ren'Py's owning thread and Android view
operations on Android's UI thread.

Keep player rollback removed and camera, location, and audio recording disabled
unless the user changes those choices. Do not copy the donor's requirement to
bundle all 19 Flet extensions into this fork.

Run `python3 -m unittest discover -s tests -t . -v` for host checks.
After engine/screens changes, assemble the SDK, compile/lint the example, and
run `scripts/check_native.py` with the real modified SDK. Mark unavailable
Android or physical-device checks as unverified; packaged source and successful
imports are not runtime acceptance.

Keep changes reviewable on a branch. Do not merge a pull request or publish
an application release unless the user authorizes that step.
