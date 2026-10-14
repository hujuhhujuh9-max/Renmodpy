import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from build_sdk import assemble
from prepare import extract_archive, verify_archive


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_locked_archive_rejects_changed_bytes(self):
        path = self.root / "input.zip"
        path.write_bytes(b"locked")
        spec = {"size_bytes": 6, "sha256": hashlib.sha256(b"locked").hexdigest()}
        verify_archive(path, spec)
        path.write_bytes(b"edited")
        with self.assertRaisesRegex(ValueError, "checksum"):
            verify_archive(path, spec)

    def test_zip_and_tar_cannot_escape_the_stage(self):
        archive = self.root / "input.zip"
        with zipfile.ZipFile(archive, "w") as zip_stream:
            zip_stream.writestr("../outside", b"unsafe")
        with self.assertRaises(ValueError):
            extract_archive(archive, self.root / "stage", "zip")
        with tarfile.open(self.root / "input.tar", "w") as tar:
            entry = tarfile.TarInfo("../outside")
            entry.size = 6
            tar.addfile(entry, io.BytesIO(b"unsafe"))
        with self.assertRaises(tarfile.TarError):
            extract_archive(self.root / "input.tar", self.root / "stage", "tar")
        self.assertFalse((self.root / "outside").exists())

    def test_assembly_integrates_engine_and_refuses_to_replace_an_sdk(self):
        source = self.root / "input"
        (source / "renpy/common").mkdir(parents=True)
        (source / "renpy.sh").write_text("launcher")
        (source / "renpy/common/00start.rpyc").write_bytes(b"stale compiled startup")
        inputs = type("Inputs", (), {"components": {"renpy": {"version": "8.5.3"}},
                                     "setup": lambda self, name: source})()
        output = self.root / "output"
        # The fixture has no upstream engine sources. Real patch application
        # and startup/load behavior are exercised by the native-engine check.
        with patch("build_sdk.subprocess.run"):
            assemble(inputs, output, with_android=False)
        self.assertTrue((output / "renpy/renmodpy/records.py").is_file())
        self.assertTrue((output / "renpy/common/00renmodpy.rpy").is_file())
        self.assertTrue((output / "renmodpy-example/game/script.rpy").is_file())
        receipt = json.loads((output / "renmodpy-build.json").read_text())
        self.assertFalse(receipt["android_packaging"])
        self.assertIn("engine/common/00renmodpy.rpy", receipt["source_files"])
        self.assertIn("engine/patches/startup-load-boundary.patch", receipt["source_files"])
        self.assertIn("engine/patches/mobile-recovery-preservation.patch", receipt["source_files"])
        self.assertIn("engine/patches/mobile-suspend-before-render.patch", receipt["source_files"])
        self.assertFalse((output / "renpy/common/00start.rpyc").exists())
        with self.assertRaises(FileExistsError):
            assemble(inputs, output, with_android=False)
        self.assertEqual((output / "renpy.sh").read_text(), "launcher")

    def test_failed_assembly_does_not_publish_a_partial_sdk(self):
        source = self.root / "input"
        source.mkdir()
        inputs = type("Inputs", (), {"components": {},
                                     "setup": lambda self, name: source})()
        output = self.root / "output"
        with patch("build_sdk.shutil.copytree", side_effect=OSError("full disk")):
            with self.assertRaises(OSError):
                assemble(inputs, output, with_android=False)
        self.assertFalse(output.exists())
        self.assertFalse(list(self.root.glob("renmodpy-*")))

    def test_rejected_engine_patch_does_not_publish_an_sdk(self):
        source = self.root / "input"
        source.mkdir()
        inputs = type("Inputs", (), {"components": {},
                                     "setup": lambda self, name: source})()
        output = self.root / "output"
        with patch("build_sdk.subprocess.run", side_effect=subprocess.CalledProcessError(1, "patch")):
            with self.assertRaises(subprocess.CalledProcessError):
                assemble(inputs, output, with_android=False)
        self.assertFalse(output.exists())
        self.assertFalse(list(self.root.glob("renmodpy-*")))
