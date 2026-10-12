#!/usr/bin/env python3
"""Create an ordinary Android RenModPy project from the assembled example."""
import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile


def create_project(sdk, destination, name, package):
    sdk, destination = Path(sdk).resolve(), Path(destination).absolute()
    if not isinstance(name, str) or not name.strip() or len(name) > 80 or not name.isprintable():
        raise ValueError("Use a printable project name of 1–80 characters.")
    if not re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){2,}", package):
        raise ValueError("Use a lowercase Android package such as org.example.story.")
    reserved = {"class", "int", "new", "for", "if", "else", "return", "package", "import", "public", "private", "static", "void", "null", "true", "false"}
    if any(part in reserved for part in package.split(".")):
        raise ValueError("Android package components cannot be Java keywords.")
    if destination.exists():
        raise FileExistsError("Project directory already exists: " + str(destination))
    if not (sdk / "renpy/renmodpy/__init__.py").is_file():
        raise ValueError("Use an assembled RenModPy SDK.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".renmodpy-project-", dir=destination.parent) as directory:
        stage = Path(directory) / "project"
        shutil.copytree(sdk / "renmodpy-example", stage, ignore=shutil.ignore_patterns(
            "*.rpyc", "*.pyc", "__pycache__", "saves", "log.txt", "traceback.txt", "errors.txt",
            "*.keystore", "*.jks", "android_probe.*", "*_probe.rpy", "*_probe.rpyc"))
        android = json.loads((stage / ".android.json").read_text())
        android.update(package=package, name=name, icon_name=name, version="0.1.0", numeric_version=1)
        (stage / ".android.json").write_text(json.dumps(android, indent=2, ensure_ascii=False) + "\n")
        script = stage / "game/script.rpy"
        text = script.read_text()
        for setting, value in (("config.name", name), ("config.save_directory", package),
                               ("build.name", package.replace(".", "_"))):
            text = re.sub(r"(?m)^define " + re.escape(setting) + r" = .*?$",
                          lambda match: "define " + setting + " = " + json.dumps(value, ensure_ascii=False), text)
        script.write_text(text)
        # Refuse an unexpectedly created destination before publishing.
        if destination.exists():
            raise FileExistsError("Project directory already exists: " + str(destination))
        stage.rename(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--sdk", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--name", required=True)
    parser.add_argument("--package", required=True)
    args = parser.parse_args()
    print(create_project(args.sdk, args.destination, args.name, args.package))


if __name__ == "__main__":
    main()
