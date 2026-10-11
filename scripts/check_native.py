#!/usr/bin/env python3
"""Exercise the assembled native engine; never mutate the source example."""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


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
        for filename in ("passed.json", "checkpoint.json"):
            (output / filename).unlink(missing_ok=True)
        run("compile", ["compile"])
        run("lint", ["lint"])
        run("save", RENMODPY_CHECK_PHASE="save")
        checkpoint = json.loads((output / "checkpoint.json").read_text())
        run("reload", RENMODPY_CHECK_PHASE="reload", RENPY_AUTO_LOAD=checkpoint["slot"])
        receipt = json.loads((output / "passed.json").read_text())
        if receipt.get("result") != "passed":
            raise RuntimeError("Native probe did not finish its assertions.")
        for screen in ("home", "records", "saves", "dialogue", "story-home", "saved-catalog",
                       "tactics", "reloaded-tactics"):
            if not (output / (screen + ".png")).is_file():
                raise RuntimeError(f"Missing rendered screen: {screen}")
        # Use a clean project so the Android distribution never includes the
        # validation driver or its environment-dependent startup override.
        with tempfile.TemporaryDirectory(prefix="android-", dir=output) as package_directory:
            package_root = Path(package_directory)
            package_project = package_root / "project"
            shutil.copytree(sdk / "renmodpy-example", package_project, ignore=IGNORE_PROJECT)
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
