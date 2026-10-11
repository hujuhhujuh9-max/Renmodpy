# RenModPy vision

Recorded from the user's instructions on 2026-10-11. The original wording is
preserved in [user-prompts.md](user-prompts.md). This document explains the
intended product; [feature-parity.md](feature-parity.md) records implementation
and evidence. The user's later instructions take precedence.

## One continuous Android application

RenModPy is a modified Ren'Py SDK focused on Android. Its quality benchmark is
RenFletPy from `hujuhhujuh9-max/SDK-`. Reuse useful donor behavior and code,
changing it as needed to fit Ren'Py and Python.

The user renewed work in Codex on 2026-10-11 and asked RenModPy to carry
forward SDK-'s strengths as SDK- development ends. Continue the existing
foundation and verify its Android behavior before expanding the feature set.

Home, application screens, dialogue, choices and activities belong to one
continuous application and project. Ren'Py/SDL owns startup, rendering, story
flow and the Python interpreter. Added features belong inside the modified
engine and ship in the same Android APK.

Do not turn the project into several apps, independent runtimes, or competing
authoring formats. Built-in Python modules, Ren'Py screens and Android native
code behind the engine's Python API are compatible with this vision. Flet,
Flutter and Dart do not become separate runtime owners.

## What matters

- Preserve Ren'Py's useful Python runtime, story syntax, visual-novel dialogue
  and character systems, and story-aware saves.
- Make Home, Return, durable Resume, Records and named-save screens fit the
  same live story/application session.
- Aim for RenFletPy's practical capabilities and quality. Simply moving code
  into one engine does not establish equivalent behavior.
- Treat tactics as a lower-priority example, not the product's central goal.
- WebView is outside the user's interest. Rive, Lottie and complex controls
  require a useful product case before adding their runtimes.

Godot was considered during the discussion. The user subsequently chose to
continue RenModPy. Dictated variants such as “Ren Mod Pi” and “Ren flip pi”
refer to RenModPy and RenFletPy in context.

Application Records must stay current when an older story save loads. This
data remains part of the same application even though it is stored separately
from a story snapshot. Replay should reset story state while retaining
application data, reading preferences and user checkpoints.

The repository currently retains the donor's removed player rollback and its
limits on camera, location and audio recording. These are existing project
constraints, not new interpretations of the prompts.

## Android acceptance and handoff

The user expected emulator testing. A Linux engine-test pass or successful
Android distribution step is insufficient to claim Android runtime acceptance.
Build the APK, install it on a real Android emulator or device, exercise actual
Android input and verify saves, application data and restart behavior. Report
what was run and what remains unverified.

Before handing the project to Codex, the user's operational instruction was:

> Install and if you have trouble stop, because I can ask codex and it has a better environment space.

That session stopped and preserved the prompts, vision and exact blocker.
The later Codex continuation authorizes renewed work. Keep installation and
runtime evidence distinct, and preserve a new environment blocker rather than
retrying environment workarounds indefinitely. See [codex-handoff.md](codex-handoff.md)
for the current implementation and checks.
