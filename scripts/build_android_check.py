#!/usr/bin/env python3
"""Build a disposable validation APK with the assembled SDK's ordinary RAPT path."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / ".renmodpy-build/android-build")
    args = parser.parse_args()
    sdk, output = args.sdk.resolve(), args.output.resolve()
    android_sdk = Path(os.environ["ANDROID_HOME"]).resolve()
    if not (android_sdk / "platforms/android-36/android.jar").is_file():
        raise RuntimeError("Install Android SDK platform 36 before building.")
    output.mkdir(parents=True, exist_ok=True)
    project = output / "project"
    shutil.copytree(sdk / "renmodpy-example", project, ignore=shutil.ignore_patterns(
        "*.rpyc", "saves", "log.txt", "traceback.txt", "errors.txt"))
    shutil.copy2(ROOT / "scripts/android_probe.rpy", project / "game/android_probe.rpy")
    shutil.copy2(ROOT / "scripts/android_services_probe.rpy", project / "game/android_services_probe.rpy")
    (sdk / "rapt/sdk.txt").write_text(str(android_sdk) + "\n")
    # This key belongs only to the disposable CI example, never to a release.
    subprocess.run(["keytool", "-genkeypair", "-keystore", str(project / "android.keystore"),
        "-alias", "android", "-keyalg", "RSA", "-keysize", "2048", "-validity", "30",
        "-storepass", "android", "-keypass", "android", "-dname", "CN=RenModPy CI"], check=True)
    shutil.copy2(project / "android.keystore", project / "bundle.keystore")
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", RENPY_RENDERER="sw",
        RENMODPY_ANDROID_PROBE_DIRECTORY=str(output / "host-observer"))
    env["LD_LIBRARY_PATH"] = str(sdk / "lib/py3-linux-x86_64") + ":" + env.get("LD_LIBRARY_PATH", "")
    with (output / "build.log").open("w") as log:
        result = subprocess.run([str(sdk / "renpy.sh"), str(sdk / "launcher"), "android_build",
            str(project), "--destination", str(output / "apks")], env=env, stdout=log,
            stderr=subprocess.STDOUT, timeout=900)
    apks = list((output / "apks").glob("*.apk"))
    if result.returncode or len(apks) != 1:
        print((output / "build.log").read_text(), flush=True)
        raise RuntimeError("RAPT did not produce one validation APK.")
    subprocess.run([str(sdk / "rapt/project/gradlew"), "--stop"], check=False)
    apk = apks[0]
    with apk.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    (output / "build.json").write_text(json.dumps({"apk": str(apk), "package": "org.renmodpy.example",
        "sha256": checksum, "validation_fixture": True,
        "release": False}, indent=2) + "\n")
    print(f"Android validation APK: {apk}", flush=True)


if __name__ == "__main__":
    main()
