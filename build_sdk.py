#!/usr/bin/env python3
"""Assemble one modified RenModPy SDK from pinned Ren'Py inputs."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from prepare import BuildInputs, ROOT


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_inventory():
    files = {}
    for directory in ("engine", "examples/native-app"):
        for path in sorted((ROOT / directory).rglob("*")):
            if (path.is_file() and "__pycache__" not in path.parts
                    and path.suffix not in (".pyc", ".rpyc")
                    and "saves" not in path.parts
                    and path.name not in ("log.txt", "traceback.txt", "errors.txt")):
                files[path.relative_to(ROOT).as_posix()] = file_hash(path)
    files["sdk-lock.json"] = file_hash(ROOT / "sdk-lock.json")
    return files


def assemble(inputs, output, *, with_android=True):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}. Choose a fresh --output.")
    output.parent.mkdir(parents=True, exist_ok=True)
    source = inputs.setup("renpy")
    if with_android:
        inputs.setup("renpy-rapt")
    stage = Path(tempfile.mkdtemp(prefix="renmodpy-", dir=output.parent))
    try:
        sdk = stage / "sdk"
        shutil.copytree(source, sdk, ignore=shutil.ignore_patterns("rapt", "__pycache__"),
                        symlinks=True)
        for patch in sorted((ROOT / "engine/patches").glob("*.patch")):
            subprocess.run(["patch", "--batch", "--forward", "-p1"],
                           input=patch.read_bytes(), cwd=sdk, check=True)
        # Engine patches must be compiled from their changed source rather
        # than a compiled common script retained by a previous SDK run.
        (sdk / "renpy/common/00start.rpyc").unlink(missing_ok=True)
        shutil.copytree(ROOT / "engine/python/renmodpy", sdk / "renpy/renmodpy",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for path in (ROOT / "engine/common").glob("*.rpy"):
            shutil.copy2(path, sdk / "renpy/common" / path.name)
        shutil.copytree(ROOT / "examples/native-app", sdk / "renmodpy-example",
                        ignore=shutil.ignore_patterns("__pycache__", "*.rpyc", "saves",
                                                      "log.txt", "traceback.txt", "errors.txt"))
        if with_android:
            shutil.copytree(inputs.sdk_root("renpy-rapt"), sdk / "rapt", symlinks=True)
            for patch in inputs.components["renpy-rapt"].get("patches", []):
                subprocess.run(["patch", "--batch", "--forward", "-p1"],
                               input=inputs.branch_file("renpy-rapt", patch["path"], patch["sha256"]),
                               cwd=sdk / "rapt", check=True)
            for patch in sorted((ROOT / "engine/android/patches").glob("*.patch")):
                subprocess.run(["patch", "--batch", "--forward", "-p1"],
                               input=patch.read_bytes(), cwd=sdk / "rapt", check=True)
            shutil.copytree(ROOT / "engine/android/java",
                            sdk / "rapt/prototype/renpyandroid/src/main/java", dirs_exist_ok=True)
        notices = sdk / "renmodpy-notices"
        notices.mkdir()
        shutil.copy2(ROOT / "LICENSE", notices / "PROJECT-LICENSE.txt")
        shutil.copy2(ROOT / "docs/provenance.md", notices / "PROVENANCE.md")
        for component in ("renpy", "renpy-rapt") if with_android else ("renpy",):
            for notice in inputs.components[component].get("notices", []):
                (notices / (component + "-" + Path(notice["path"]).name)).write_bytes(
                    inputs.branch_file(component, notice["path"], notice["sha256"]))
        receipt = {"product": "RenModPy", "version": "0.1.0", "target": "android",
                   "renpy_version": inputs.components["renpy"]["version"],
                   "android_packaging": with_android, "source_files": source_inventory(),
                   "components": inputs.components}
        (sdk / "renmodpy-build.json").write_text(json.dumps(receipt, indent=2) + "\n")
        sdk.rename(output)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    print(f"RenModPy SDK: {output}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".renmodpy-build")
    parser.add_argument("--archives", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / ".renmodpy-build/renmodpy-sdk")
    parser.add_argument("--host-check-only", action="store_true",
                        help="Omit RAPT for Linux validation; this does not build an APK.")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 12) or sys.platform != "linux":
        parser.error("SDK assembly requires Linux and Python 3.12 or later.")
    inputs = BuildInputs(args.cache_dir, args.archives)
    assemble(inputs, args.output, with_android=not args.host_check_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
