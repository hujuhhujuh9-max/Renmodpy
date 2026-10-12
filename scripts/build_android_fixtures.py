#!/usr/bin/env python3
"""Build an offline receiver, document provider and IME for disposable CI only."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".renmodpy-build/android-fixtures")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "scripts/fixtures"
    android_sdk = Path(os.environ["ANDROID_HOME"])
    tools = android_sdk / "build-tools/36.0.0"
    android_jar = android_sdk / "platforms/android-36/android.jar"
    classes, dex = output / "classes", output / "dex"
    classes.mkdir(exist_ok=True); dex.mkdir(exist_ok=True)
    with (output / "build.log").open("w") as log:
        def run(arguments):
            subprocess.run([str(value) for value in arguments], check=True, stdout=log, stderr=subprocess.STDOUT)
        run(["javac", "-encoding", "UTF-8", "-source", "17", "-target", "17", "-classpath", android_jar,
             "-d", classes, *sorted((source / "java").rglob("*.java"))])
        run([tools / "d8", "--min-api", "23", "--lib", android_jar, "--output", dex, *sorted(classes.rglob("*.class"))])
        run([tools / "aapt2", "compile", "--dir", source / "res", "-o", output / "resources.zip"])
        run([tools / "aapt2", "link", "-I", android_jar, "--manifest", source / "AndroidManifest.xml",
             "-o", output / "base.apk", output / "resources.zip"])
        with zipfile.ZipFile(output / "base.apk", "a") as archive:
            archive.write(dex / "classes.dex", "classes.dex")
        run([tools / "zipalign", "-f", "4", output / "base.apk", output / "aligned.apk"])
        # The product APK's disposable key is used only to sign this fixture.
        key = ROOT / ".renmodpy-build/android-build/project/android.keystore"
        run([tools / "apksigner", "sign", "--ks", key, "--ks-key-alias", "android", "--ks-pass", "pass:android",
             "--key-pass", "pass:android", "--out", output / "fixtures.apk", output / "aligned.apk"])
    apk = output / "fixtures.apk"
    (output / "build.json").write_text(json.dumps({"package": "org.renmodpy.validation", "apk": str(apk),
        "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(), "validation_fixture": True,
        "release": False, "permissions": []}, indent=2) + "\n")
    print("Built offline Android validation fixtures", flush=True)


if __name__ == "__main__":
    main()
