#!/usr/bin/env python3
"""Install the validation APK and exercise real Android input on a rooted CI emulator."""

import argparse
import json
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "org.renmodpy.example"
STATE = f"/data/user/0/{PACKAGE}/files/renmodpy-probe/state.json"
ACTIVITY = PACKAGE + "/org.renpy.android.PythonSDLActivity"


def adb(*arguments, check=True, timeout=45):
    return subprocess.run(["adb", *arguments], capture_output=True, check=check, timeout=timeout)


def run(apk, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "passed.json").unlink(missing_ok=True)
    latest = {}
    checks = []

    def state():
        nonlocal latest
        result = adb("exec-out", "cat", STATE, check=False)
        if result.returncode == 0:
            try:
                latest = json.loads(result.stdout)
            except ValueError:
                pass
            return latest
        return {}

    def wait(predicate, message, timeout=60):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            current = state()
            if current and predicate(current):
                return current
            time.sleep(0.4)
        raise RuntimeError(message + "; state: " + repr(latest))

    def screen(name):
        return wait(lambda s: name in s["screens"], "Screen did not open: " + name)

    def capture(name):
        (output / (name + ".png")).write_bytes(adb("exec-out", "screencap", "-p").stdout)

    def tap(name):
        current = wait(lambda s: any(b["name"] == name for b in s["buttons"]),
                       "No tappable control: " + name)
        button = next(b for b in current["buttons"] if b["name"] == name)
        x, y, width, height = button["rect"]
        physical_width, physical_height = current["physical_size"]
        virtual_width, virtual_height = current["virtual_size"]
        scale = min(physical_width / virtual_width, physical_height / virtual_height)
        x = (physical_width - virtual_width * scale) / 2 + (x + width / 2) * scale
        y = (physical_height - virtual_height * scale) / 2 + (y + height / 2) * scale
        adb("shell", "input", "tap", str(round(x)), str(round(y)))

    def enter(field, text):
        if state().get("editable_field") != field:
            tap("field:" + field)
            wait(lambda s: s.get("editable_field") == field, "Field did not receive focus")
        adb("shell", "input", "text", text.replace(" ", "%s"))
        wait(lambda s: s.get("draft", {}).get(field) == text, "Android text input did not reach the form")

    def home():
        tap("Home")
        screen("renmodpy_home")

    try:
        adb("wait-for-device", timeout=180)
        deadline = time.monotonic() + 180
        while adb("shell", "getprop", "sys.boot_completed", check=False).stdout.strip() != b"1":
            if time.monotonic() >= deadline:
                raise RuntimeError("Android emulator did not finish booting.")
            time.sleep(1)
        if adb("shell", "getprop", "ro.kernel.qemu").stdout.strip() != b"1":
            raise RuntimeError("Use a disposable emulator; this check clears the example's app data.")
        adb("root")
        adb("wait-for-device")
        if adb("shell", "id", "-u").stdout.strip() != b"0":
            raise RuntimeError("The validation observer requires a rooted emulator.")
        for namespace, name in (("global", "device_provisioned"), ("secure", "user_setup_complete"),
                                ("secure", "show_ime_with_hard_keyboard")):
            adb("shell", "settings", "put", namespace, name, "1")
        adb("shell", "settings", "put", "secure", "immersive_mode_confirmations", "confirmed")
        adb("shell", "input", "keyevent", "224")
        adb("shell", "wm", "dismiss-keyguard")
        adb("shell", "wm", "size", "720x1280")
        adb("shell", "wm", "density", "160")
        adb("logcat", "-c")
        adb("install", "-r", str(apk))
        adb("shell", "pm", "clear", PACKAGE)
        adb("shell", "am", "start", "-W", "-n", ACTIVITY)
        initial = screen("main_menu")
        assert initial["android"], "The APK did not run the Android runtime"
        capture("home")
        tap("Start story")
        original = screen("say")
        original_history = original["history"]
        assert "folded note" in original_history[-1]
        capture("dialogue")
        home()
        wait(lambda s: s["resume"] is not None, "Home did not create a resume bookmark")
        tap("Quick save")
        wait(lambda s: s["quick"], "Quick save was not created")
        tap("Reading settings")
        screen("renmodpy_settings")
        tap("Larger")
        wait(lambda s: s["font_size"] == 1.25, "Larger reading setting did not apply")
        tap("Instant")
        wait(lambda s: s["text_cps"] == 0, "Instant dialogue setting did not apply")
        capture("settings")
        home()
        tap("Story history")
        history = screen("renmodpy_history")
        assert history["history"] == original_history
        capture("history")
        home()
        tap("Records")
        screen("renmodpy_records")
        enter("title", "Emulator note")
        enter("body", "Created after the quick save")
        capture("record-input")
        # Deselect the native input to close the IME before tapping form actions.
        tap("field:body")
        wait(lambda s: s.get("editable_field") is None, "Input stayed active")
        tap("Add record")
        wait(lambda s: len(s["records"]) == 1, "Record was not saved")
        capture("records")
        home()
        tap("Resume story")
        resumed = screen("say")
        assert resumed["history"] == original_history
        checks.append("Android taps move through Home/history/settings/Records and return to the exact dialogue")
        boot = resumed["boot"]
        adb("shell", "am", "force-stop", PACKAGE)
        adb("shell", "am", "start", "-W", "-n", ACTIVITY)
        wait(lambda s: s["boot"] != boot and "main_menu" in s["screens"], "App did not restart")
        tap("Resume story")
        restored = screen("say")
        assert restored["history"] == original_history and len(restored["records"]) == 1
        assert restored["font_size"] == 1.25 and restored["text_cps"] == 0
        capture("restarted-dialogue")
        checks.append("Force-stop/relaunch and durable Resume preserve story position, private Records and reading preferences")
        home()
        tap("Quick load")
        screen("confirm")
        tap("Yes")
        loaded = screen("say")
        assert loaded["history"] == original_history and len(loaded["records"]) == 1
        assert loaded["font_size"] == 1.25 and loaded["text_cps"] == 0
        capture("quick-loaded-dialogue")
        checks.append("Loading an older Android quick save keeps newer application Records and reading preferences")
        receipt = {"result": "passed", "platform": "Android emulator", "engine": loaded["engine"],
            "api": adb("shell", "getprop", "ro.build.version.sdk").stdout.decode().strip(),
            "abi": adb("shell", "getprop", "ro.product.cpu.abi").stdout.decode().strip(),
            "checks": checks, "physical_device": False, "release": False}
        (output / "passed.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2), flush=True)
    finally:
        (output / "last-state.json").write_text(json.dumps(latest, indent=2) + "\n")
        (output / "logcat.log").write_bytes(adb("logcat", "-d", check=False).stdout)
        capture("last-screen")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=ROOT / ".renmodpy-build/android-build")
    parser.add_argument("--output", type=Path, default=ROOT / ".renmodpy-build/android-check")
    args = parser.parse_args()
    build = json.loads((args.build / "build.json").read_text())
    run(Path(build["apk"]), args.output)


if __name__ == "__main__":
    main()
