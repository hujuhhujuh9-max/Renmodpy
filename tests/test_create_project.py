import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.create_project import create_project


class CreateProjectTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.sdk = self.root / "sdk"
        (self.sdk / "renpy/renmodpy").mkdir(parents=True)
        (self.sdk / "renpy/renmodpy/__init__.py").write_text("")
        source = Path(__file__).resolve().parents[1] / "examples/native-app"
        import shutil
        shutil.copytree(source, self.sdk / "renmodpy-example")

    def test_fresh_project_keeps_media_and_excludes_runtime_data_keys_and_observers(self):
        template = self.sdk / "renmodpy-example"
        (template / "android.keystore").write_text("private key")
        (template / "game/android_probe.rpy").write_text("test observer")
        (template / "game/script.rpyc").write_bytes(b"cached script")
        project = create_project(self.sdk, self.root / "project", 'Café "Stories"', "org.example.stories")
        config = json.loads((project / ".android.json").read_text())
        self.assertEqual(config["package"], "org.example.stories")
        self.assertEqual(config["name"], 'Café "Stories"')
        self.assertTrue((project / "game/media/colors.webm").is_file())
        self.assertFalse((project / "android.keystore").exists())
        self.assertFalse((project / "game/android_probe.rpy").exists())
        self.assertFalse((project / "game/script.rpyc").exists())
        self.assertIn('define config.save_directory = "org.example.stories"', (project / "game/script.rpy").read_text())
        with self.assertRaises(FileExistsError):
            create_project(self.sdk, project, "Other", "org.example.other")
        self.assertEqual(json.loads((project / ".android.json").read_text())["package"], "org.example.stories")

    def test_invalid_identity_and_failed_copy_never_publish_a_partial_project(self):
        destination = self.root / "project"
        for name, package in (("", "org.example.story"), ("Story", "org.class.story"), ("Story", "org.Example.story")):
            with self.assertRaises(ValueError):
                create_project(self.sdk, destination, name, package)
        with patch("scripts.create_project.shutil.copytree", side_effect=OSError("full disk")):
            with self.assertRaises(OSError):
                create_project(self.sdk, destination, "Story", "org.example.story")
        self.assertFalse(destination.exists())
        self.assertFalse(list(self.root.glob(".renmodpy-project-*")))
