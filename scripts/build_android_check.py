#!/usr/bin/env python3
"""Build a disposable validation APK with the assembled SDK's ordinary RAPT path."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import re
import time
import zipfile
import tarfile
from create_project import create_project


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
    create_project(sdk, project, "RenModPy Native Example", "org.renmodpy.example")
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
    def build(source, destination, *, bundle=False):
        with (output / "build.log").open("a") as log:
            result = subprocess.run([str(sdk / "renpy.sh"), str(sdk / "launcher"), "android_build",
                str(source), "--destination", str(destination), *(["--bundle"] if bundle else [])],
                env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        artifacts = list(destination.glob("*.aab" if bundle else "*.apk"))
        if result.returncode or len(artifacts) != 1:
            print((output / "build.log").read_text(), flush=True)
            raise RuntimeError("RAPT did not produce one signed Android artifact.")
        return artifacts[0]

    apk = build(project, output / "apks")
    upgrade = output / "upgrade-project"
    # Ren'Py merges statement identities from the previous compiled scripts.
    # Dropping them makes old saves fall back to an earlier surviving label.
    shutil.copytree(project, upgrade, ignore=shutil.ignore_patterns("saves", "log.txt", "errors.txt", "traceback.txt"))
    configuration = json.loads((upgrade / ".android.json").read_text())
    configuration.update(version="0.1.1", numeric_version=int(time.time()) + 1)
    (upgrade / ".android.json").write_text(json.dumps(configuration, indent=2) + "\n")
    script = upgrade / "game/script.rpy"
    script.write_text(script.read_text().replace('define config.version = "0.1.0"', 'define config.version = "0.1.1"'))
    upgrade_apk = build(upgrade, output / "upgrades")
    clean_project = create_project(sdk, output / "fresh-project", "Fresh RenModPy Story", "org.renmodpy.packaging")
    clean_config = json.loads((clean_project / ".android.json").read_text())
    clean_config["renmodpy_deep_links"] = False
    (clean_project / ".android.json").write_text(json.dumps(clean_config, indent=2) + "\n")
    shutil.copy2(project / "android.keystore", clean_project / "android.keystore")
    shutil.copy2(project / "bundle.keystore", clean_project / "bundle.keystore")
    aab = build(clean_project, output / "bundles", bundle=True)
    android_tools = android_sdk / "build-tools/36.0.0"
    def apk_certificate(path):
        result = subprocess.run([str(android_tools / "apksigner"), "verify", "--print-certs", str(path)],
                                capture_output=True, text=True, check=True)
        return re.search(r"certificate SHA-256 digest: ([0-9a-f]+)", result.stdout).group(1)
    certificate = apk_certificate(apk)
    assert apk_certificate(upgrade_apk) == certificate
    def apk_metadata(path):
        badging = subprocess.run([str(android_tools / "aapt2"), "dump", "badging", str(path)],
                                 capture_output=True, text=True, check=True).stdout
        package, code, version = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badging).groups()
        permissions = re.findall(r"uses-permission: name='([^']+)'", badging)
        manifest = subprocess.run([str(android_tools / "aapt2"), "dump", "xmltree", str(path),
            "--file", "AndroidManifest.xml"], capture_output=True, text=True, check=True).stdout
        assert "android.intent.action.VIEW" in manifest and "android.intent.category.BROWSABLE" in manifest
        assert "org.renmodpy.deep_links" in manifest and '"' + package + '"' in manifest and '"records"' in manifest
        assert "android.permission.WRITE_EXTERNAL_STORAGE" not in permissions
        assert not set(permissions) & {"android.permission.CAMERA", "android.permission.RECORD_AUDIO", "android.permission.ACCESS_FINE_LOCATION"}
        return {"package": package, "version_code": int(code), "version": version, "permissions": permissions,
                "record_link_scheme": package, "record_links_enabled": True}
    base_metadata, upgrade_metadata = apk_metadata(apk), apk_metadata(upgrade_apk)
    assert base_metadata["package"] == upgrade_metadata["package"] == "org.renmodpy.example"
    assert upgrade_metadata["version_code"] > base_metadata["version_code"]
    assert (base_metadata["version"], upgrade_metadata["version"]) == ("0.1.0", "0.1.1")
    verified = subprocess.run(["jarsigner", "-verify", str(aab)], capture_output=True, text=True, check=True)
    assert "jar verified." in verified.stdout
    bundle_cert = subprocess.run(["keytool", "-printcert", "-jarfile", str(aab)], capture_output=True, text=True, check=True)
    assert re.search(r"SHA256: ([0-9A-F:]+)", bundle_cert.stdout).group(1).replace(":", "").lower() == certificate
    with zipfile.ZipFile(aab) as archive:
        names = archive.namelist()
        assert "base/manifest/AndroidManifest.xml" in names and "base/dex/classes.dex" in names
        clean_manifest = archive.read("base/manifest/AndroidManifest.xml")
        assert b"org.renmodpy.deep_links" not in clean_manifest and b"android.intent.action.VIEW" not in clean_manifest
        assert any(name.startswith("base/lib/arm64-v8a/") for name in names)
        assert any(name.startswith("base/lib/x86_64/") for name in names)
        assert not any("probe" in name for name in names if name.startswith("base/assets/"))
        with tarfile.open(fileobj=io.BytesIO(archive.read("base/assets/private.mp3")), mode="r:gz") as private:
            private_names = private.getnames()
            assert any("renpy/renmodpy" in name and "services" in name for name in private_names)
            assert not any("android_probe" in name or "native_probe" in name for name in private_names)
    assert not list((clean_project / "game").glob("*probe*"))
    subprocess.run([str(sdk / "rapt/project/gradlew"), "--stop"], check=False)
    with apk.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    (output / "build.json").write_text(json.dumps({"apk": str(apk), "package": "org.renmodpy.example",
        "sha256": checksum, "validation_fixture": True,
        "upgrade_apk": str(upgrade_apk), "upgrade_sha256": hashlib.sha256(upgrade_apk.read_bytes()).hexdigest(),
        "aab": str(aab), "aab_sha256": hashlib.sha256(aab.read_bytes()).hexdigest(),
        "signer_sha256": certificate, "same_key_upgrade": True,
        "base_metadata": base_metadata, "upgrade_metadata": upgrade_metadata,
        "fresh_project_package": "org.renmodpy.packaging", "fresh_project_has_observers": False,
        "fresh_project_record_links_enabled": False,
        "aab_signed": True, "aab_abis": ["arm64-v8a", "x86_64"],
        "release": False}, indent=2) + "\n")
    print(f"Android validation APK: {apk}", flush=True)


if __name__ == "__main__":
    main()
