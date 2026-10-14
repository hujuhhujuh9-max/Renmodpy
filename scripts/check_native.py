#!/usr/bin/env python3
"""Exercise the assembled native engine; never mutate the source example."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import xml.etree.ElementTree as ET
from pathlib import Path
from media_evidence import inspect_frames
from create_project import create_project


ROOT = Path(__file__).resolve().parents[1]
IGNORE_PROJECT = shutil.ignore_patterns("*.rpyc", "saves", "log.txt", "traceback.txt", "errors.txt")


def check(sdk, output):
    sdk, output = Path(sdk).resolve(), Path(output).resolve()
    if not (sdk / "renpy/renmodpy/__init__.py").is_file():
        raise ValueError("Use an assembled RenModPy SDK, not an upstream SDK.")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="project-", dir=output) as directory:
        project = Path(directory)
        shutil.copytree(sdk / "renmodpy-example", project, dirs_exist_ok=True,
                        ignore=IGNORE_PROJECT)
        shutil.copy2(ROOT / "scripts/native_probe.rpy", project / "game/native_probe.rpy")
        env = dict(os.environ, RENMODPY_CHECK_OUTPUT=str(output),
                   RENMODPY_CHECK_SAVEDIR=str(project / "saves"),
                   RENPY_SKIP_MAIN_MENU="1", RENPY_SKIP_SPLASHSCREEN="1",
                   SDL_AUDIODRIVER="dummy", LIBGL_ALWAYS_SOFTWARE="1")
        # Keep the validation executable's native dependencies discoverable
        # even on hosts that relocate executable paths through a filesystem proxy.
        env["LD_LIBRARY_PATH"] = str(sdk / "lib/py3-linux-x86_64") + (
            ":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
        if not env.get("DISPLAY") and not env.get("SDL_VIDEODRIVER"):
            env.update(SDL_VIDEODRIVER="dummy", RENPY_RENDERER="sw")

        def run(name, arguments=(), *, project_path=project, **extra_env):
            log = output / (name + ".log")
            with log.open("w") as stream:
                try:
                    result = subprocess.run([str(sdk / "renpy.sh"), str(project_path), *arguments],
                                            env=dict(env, **extra_env), stdout=stream,
                                            stderr=subprocess.STDOUT, timeout=90)
                except subprocess.TimeoutExpired:
                    raise RuntimeError(f"Native check timed out: {name}; see {log}") from None
            for filename in ("errors.txt", "traceback.txt"):
                if (project / filename).is_file():
                    shutil.copy2(project / filename, output / (name + "-" + filename))
            if result.returncode or "Full traceback:" in log.read_text(encoding="utf-8-sig"):
                raise RuntimeError(f"Native check failed: {name} ({result.returncode}); see {log}")
            print(f"Native check: {name} passed", flush=True)

        # A failed new run must not inherit a receipt from an earlier success.
        for filename in ("passed.json", "runtime-passed.json", "checkpoint.json", "quick-passed.json", "replay-passed.json"):
            (output / filename).unlink(missing_ok=True)
        run("compile", ["compile"])
        run("lint", ["lint"])
        run("save", RENMODPY_CHECK_PHASE="save")
        checkpoint = json.loads((output / "checkpoint.json").read_text())
        run("reload", RENMODPY_CHECK_PHASE="reload", RENPY_AUTO_LOAD=checkpoint["slot"])
        receipt = json.loads((output / "runtime-passed.json").read_text())
        if receipt.get("result") != "passed":
            raise RuntimeError("Native probe did not finish its assertions.")
        remaining = list(project.rglob(checkpoint["slot"] + "*.save"))
        if remaining:
            raise RuntimeError("Named checkpoint deletion left files on disk: " + repr(remaining))
        run("quick-load", RENMODPY_CHECK_PHASE="quick", RENPY_AUTO_LOAD="renmodpy-quick")
        run("replay", RENMODPY_CHECK_PHASE="replay", RENPY_AUTO_LOAD="renmodpy-quick")
        for filename in ("quick-passed.json", "replay-passed.json"):
            if json.loads((output / filename).read_text()).get("result") != "passed":
                raise RuntimeError("Quick load or replay did not finish its assertions.")
        receipt["checks"].extend(["quick save restores exact story/board state after restart",
            "replay resets story/history while keeping records, reading settings, quick and named saves"])
        # The earlier driver skips the main menu and saves after completed
        # interactions. Also cover a save on the very first waiting dialogue
        # and load it through the ordinary Home screen in fresh processes.
        with tempfile.TemporaryDirectory(prefix="startup-", dir=output) as directory:
            startup_project = Path(directory)
            shutil.copytree(sdk / "renmodpy-example", startup_project, dirs_exist_ok=True,
                            ignore=IGNORE_PROJECT)
            shutil.copy2(ROOT / "scripts/startup_probe.rpy", startup_project / "game/startup_probe.rpy")
            for phase in ("save", "resume", "quick"):
                (output / ("startup-" + phase + "-passed.json")).unlink(missing_ok=True)
                run("startup-" + phase, project_path=startup_project,
                    RENMODPY_STARTUP_PHASE=phase, RENPY_SKIP_MAIN_MENU="",
                    RENMODPY_CHECK_SAVEDIR=str(startup_project / "saves"))
                if phase != "save" and json.loads((output / ("startup-" + phase + "-passed.json")).read_text()).get("result") != "passed":
                    raise RuntimeError("First-dialogue Home load did not finish: " + phase)
            with tempfile.TemporaryDirectory(prefix="startup-upgrade-", dir=output) as directory:
                upgraded_project = Path(directory)
                shutil.copytree(startup_project, upgraded_project, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns("log.txt", "traceback.txt", "errors.txt"))
                script = upgraded_project / "game/script.rpy"
                script.write_text(script.read_text().replace('define config.version = "0.1.0"', 'define config.version = "0.1.1"'))
                (output / "startup-upgrade-passed.json").unlink(missing_ok=True)
                run("startup-upgrade", project_path=upgraded_project,
                    RENMODPY_STARTUP_PHASE="upgrade", RENPY_SKIP_MAIN_MENU="",
                    RENMODPY_CHECK_SAVEDIR=str(startup_project / "saves"))
                if json.loads((output / "startup-upgrade-passed.json").read_text()).get("result") != "passed":
                    raise RuntimeError("Recompiled project upgrade did not restore the older first-dialogue save.")
        receipt["checks"].append("ordinary startup and fresh-process Home Resume/Quick load restore the first dialogue")
        receipt["checks"].append("a recompiled version update preserves statement identities and loads the previous release's first-dialogue save")
        with tempfile.TemporaryDirectory(prefix="replay-resume-", dir=output) as directory:
            replay_project = Path(directory)
            shutil.copytree(sdk / "renmodpy-example", replay_project, dirs_exist_ok=True,
                            ignore=IGNORE_PROJECT)
            shutil.copy2(ROOT / "scripts/startup_probe.rpy", replay_project / "game/startup_probe.rpy")
            for phase in ("replay-save", "replay-resume", "replay-quick"):
                (output / ("startup-" + phase + "-passed.json")).unlink(missing_ok=True)
                run("startup-" + phase, project_path=replay_project,
                    RENMODPY_STARTUP_PHASE=phase, RENPY_SKIP_MAIN_MENU="",
                    RENMODPY_CHECK_SAVEDIR=str(replay_project / "saves"))
                if phase != "replay-save" and json.loads((output / ("startup-" + phase + "-passed.json")).read_text()).get("result") != "passed":
                    raise RuntimeError("Cold load of the first dialogue saved after replay did not finish: " + phase)
        receipt["checks"].append("first-dialogue Resume and Quick load after replay survive fresh processes without rewinding Records or preferences")
        # Exercise the same save/cleanup policy used by Android's SDL suspend
        # handler. Actual OS app switching and process death run on Android.
        with tempfile.TemporaryDirectory(prefix="lifecycle-", dir=output) as directory:
            lifecycle_project = Path(directory)
            shutil.copytree(sdk / "renmodpy-example", lifecycle_project, dirs_exist_ok=True,
                            ignore=IGNORE_PROJECT)
            shutil.copy2(ROOT / "scripts/lifecycle_probe.rpy", lifecycle_project / "game/lifecycle_probe.rpy")
            (output / "lifecycle-passed.json").unlink(missing_ok=True)
            for phase in ("save-choice", "resume-choice", "resume-dialogue"):
                run("lifecycle-" + phase, project_path=lifecycle_project,
                    RENMODPY_LIFECYCLE_PHASE=phase, RENPY_SKIP_MAIN_MENU="",
                    RENMODPY_CHECK_SAVEDIR=str(lifecycle_project / "saves"))
            lifecycle = json.loads((output / "lifecycle-passed.json").read_text())
            if lifecycle.get("result") != "passed":
                raise RuntimeError("Native background recovery did not finish its assertions.")
            receipt["checks"].extend(lifecycle["checks"])
        with tempfile.TemporaryDirectory(prefix="media-", dir=output) as directory:
            media_project = Path(directory)
            shutil.copytree(sdk / "renmodpy-example", media_project, dirs_exist_ok=True, ignore=IGNORE_PROJECT)
            shutil.copy2(ROOT / "scripts/native_media_probe.rpy", media_project / "game/native_media_probe.rpy")
            (output / "media-passed.json").unlink(missing_ok=True)
            run("media", project_path=media_project)
            media = json.loads((output / "media-passed.json").read_text())
            assert media["result"] == "passed"
            media["visible_frames"] = inspect_frames(output / ("media-%d.png" % index) for index in range(6))
            (output / "media-passed.json").write_text(json.dumps(media, indent=2) + "\n")
        receipt["checks"].append("native audio playback advances, video renders both decoded colors, ATL visibly moves and media channels stop on exit")
        for screen in ("home", "records", "records-edit", "records-saved", "saves", "dialogue",
                       "story-home", "history", "settings", "saved-catalog", "replay-confirm",
                       "tactics", "reloaded-tactics"):
            if not (output / (screen + ".png")).is_file():
                raise RuntimeError(f"Missing rendered screen: {screen}")
        # Use a clean project so the Android distribution never includes the
        # validation driver or its environment-dependent startup override.
        with tempfile.TemporaryDirectory(prefix="android-", dir=output) as package_directory:
            package_root = Path(package_directory)
            package_project = package_root / "project"
            create_project(sdk, package_project, "Fresh Native Story", "org.renmodpy.freshstory")
            run("fresh-project-compile", ["compile"], project_path=package_project)
            run("fresh-project-lint", ["lint"], project_path=package_project)
            run("android-distribution", ["distribute", str(package_project), "--package", "android",
                "--dest", str(package_root / "distribution"), "--no-update"],
                project_path=sdk / "launcher")
            distributions = list((package_root / "distribution").glob("*-android"))
            if len(distributions) != 1:
                raise RuntimeError("Expected one Android distribution.")
            distribution = distributions[0]
            required = ["renpy/common/00renmodpy.rpyc", "game/script.rpyc", ".android.json"]
            for module in (ROOT / "engine/python/renmodpy").glob("*.py"):
                compiled = list((distribution / "renpy/renmodpy/__pycache__").glob(
                    module.stem + ".cpython-*.pyc"))
                if len(compiled) != 1:
                    raise RuntimeError(f"Engine module absent from Android packaging: {module.name}")
                required.append(compiled[0].relative_to(distribution).as_posix())
            for filename in required:
                if not (distribution / filename).is_file():
                    raise RuntimeError(f"Missing Android packaging input: {filename}")
            if list((distribution / "game").glob("native_probe.*")):
                raise RuntimeError("Validation driver leaked into Android packaging.")
            android = json.loads((distribution / ".android.json").read_text())
            if android["orientation"] != "portrait" or android["permissions"]:
                raise RuntimeError("Unexpected Android orientation or optional permissions.")
            receipt["android_distribution"] = {"name": distribution.name, "files": sorted(required),
                "orientation": android["orientation"], "permissions": android["permissions"],
                "apk_built": False}
        receipt["checks"].append("added engine modules/screens present in Android distribution")
        receipt["checks"].append("new project creation compiles, lints and packages with its own identity and without validation observers")
        # Use RAPT's own Jinja 2.10 and autoescape callback. A modern host
        # Jinja or XML inspection alone misses its conditional-expression bug.
        sys.path.insert(0, str(sdk / "rapt/buildlib"))
        try:
            import jinja2
            environment = jinja2.Environment(loader=jinja2.FileSystemLoader(str(sdk / "rapt")),
                autoescape=lambda filename: filename.endswith(".xml"))
            template = environment.get_template("templates/app-AndroidManifest.xml")
            android_ns = "{http://schemas.android.com/apk/res/android}"
            for enabled in (True, False):
                configuration = types.SimpleNamespace(package="org.example.link_story", orientation="portrait",
                    store="none", permissions=[], renmodpy_deep_links=enabled)
                manifest = template.render(config=configuration, manifest_extra="")
                (output / ("record-links-enabled.xml" if enabled else "record-links-disabled.xml")).write_text(manifest)
                root = ET.fromstring(manifest)
                activity = root.find("application/activity")
                assert activity.get(android_ns + "launchMode") == ("singleTask" if enabled else "singleTop")
                data = activity.findall("intent-filter/data")
                if enabled:
                    assert len(data) == 1 and data[0].get(android_ns + "scheme") == "org.example.link+story"
                    assert data[0].get(android_ns + "host") == "records"
                    assert root.find("application/meta-data").get(android_ns + "value") == "true"
                else:
                    assert not data and root.find("application/meta-data") is None
        finally:
            sys.path.pop(0)
        receipt["checks"].append("RAPT's bundled Jinja renders enabled/disabled Record-link filters, package schemes and single-task/single-top modes")
        (output / "passed.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Native receipt and screenshots: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / ".renmodpy-build/native-check")
    args = parser.parse_args()
    check(args.sdk, args.output)


if __name__ == "__main__":
    main()
