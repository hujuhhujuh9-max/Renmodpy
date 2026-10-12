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
                current = json.loads(result.stdout)
            except ValueError:
                return {}
            if isinstance(current, dict):
                latest = current
                return current
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

    def physical_point(x, y, current):
        physical_width, physical_height = current["physical_size"]
        virtual_width, virtual_height = current["virtual_size"]
        scale = min(physical_width / virtual_width, physical_height / virtual_height)
        x = (physical_width - virtual_width * scale) / 2 + x * scale
        y = (physical_height - virtual_height * scale) / 2 + y * scale
        return str(round(x)), str(round(y))

    def tap_point(x, y, current):
        adb("shell", "input", "tap", *physical_point(x, y, current))
        wait(lambda s: s["boot"] != current["boot"] or s["sequence"] > current["sequence"],
             "Android observer did not update after the tap")

    def tap(name, *, occurrence=0, scroll=None):
        def matches(current):
            return [button for button in current.get("buttons", []) if button["name"] == name]
        if scroll:
            for _ in range(5):
                current = state()
                if len(matches(current)) > occurrence:
                    break
                start, end = (1000, 300) if scroll == "down" else (300, 1000)
                adb("shell", "input", "swipe", *physical_point(660, start, current),
                    *physical_point(660, end, current), "400")
                wait(lambda s: s["sequence"] > current["sequence"], "Scroll observer did not update")
        current = wait(lambda s: len(matches(s)) > occurrence, "No tappable control: " + name)
        button = matches(current)[occurrence]
        x, y, width, height = button["rect"]
        tap_point(x + width / 2, y + height / 2, current)

    def enter(field, text):
        if state().get("editable_field") != field:
            tap("field:" + field)
            wait(lambda s: s.get("editable_field") == field, "Field did not receive focus")
        adb("shell", "input", "text", text.replace(" ", "%s"))
        wait(lambda s: s.get("input_text") == text, "Android text input did not reach the form")

    def home():
        tap("Home", scroll="up")
        screen("renmodpy_home")

    def choose(caption):
        tap_point(360, 1000, screen("say"))
        screen("choice")
        tap(caption)
        return wait(lambda s: "say" in s["screens"] and "choice" not in s["screens"]
                    and s["note_result"] is not None, "Story choice did not return to dialogue")

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
        tap("Copy line")
        wait(lambda s: s.get("clipboard") == original_history[-1], "History copy did not reach the platform clipboard")
        capture("history")
        home()
        tap("Records")
        screen("renmodpy_records")
        enter("title", "Emulator note")
        tap("Paste", occurrence=0)
        rejected = wait(lambda s: "single line" in s.get("form_message", ""), "Multiline title paste was not rejected")
        assert rejected["draft"] == {"title": "Emulator note", "body": ""}
        tap("Paste", occurrence=1)
        pasted = wait(lambda s: s.get("draft", {}).get("body") == original_history[-1],
                      "Unicode/multiline clipboard paste did not reach the record draft")
        assert "Blåbær" in pasted["draft"]["body"] and "\n" in pasted["draft"]["body"]
        assert pasted["records"] == []
        capture("record-input")
        tap("Add record")
        saved_record = wait(lambda s: len(s["records"]) == 1, "Record was not saved")["records"][0]
        assert saved_record["values"] == {"title": "Emulator note", "body": original_history[-1]}
        tap("Copy record", scroll="down")
        copied_record = "Emulator note\n\n" + original_history[-1]
        wait(lambda s: s.get("clipboard") == copied_record, "Record copy did not reach the platform clipboard")
        capture("records")
        checks.append("Native history/record copy and Unicode/multiline paste use the platform clipboard; rejected title paste preserves the draft")
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
        chosen = choose("Keep a copy")
        assert chosen["history"] != original_history and "kept a copy" in chosen["note_result"]
        home()
        tap("Quick load")
        screen("confirm")
        tap("Yes")
        loaded = screen("say")
        assert loaded["history"] == original_history and len(loaded["records"]) == 1
        assert loaded["font_size"] == 1.25 and loaded["text_cps"] == 0
        capture("quick-loaded-dialogue")
        assert loaded["note_result"] is None
        assert loaded["clipboard"] == copied_record, "Loading a story rewound the live clipboard"
        assert loaded["records"][0]["values"] == saved_record["values"]
        checks.append("Loading an older Android quick save restores the earlier dialogue/choice state while keeping newer Records and reading preferences")

        chosen = choose("Share it with Mira")
        chosen_history = chosen["history"]
        home()
        tap("Saved games")
        screen("renmodpy_saves")
        enter("save_name", "After choosing")
        tap("field:save_name")
        wait(lambda s: s.get("editable_field") is None, "Save-name input stayed active")
        tap("Create save")
        saved = wait(lambda s: len(s["saves"]) == 1, "Named checkpoint was not created")["saves"][0]
        assert saved["name"] == "After choosing" and saved["supported"]
        tap("Overwrite")
        screen("confirm")
        tap("Yes")
        wait(lambda s: len(s["saves"]) == 1 and s["saves"][0]["fingerprint"] != saved["fingerprint"],
             "Overwrite did not replace the checkpoint")
        capture("named-checkpoint")
        boot = latest["boot"]
        adb("shell", "am", "force-stop", PACKAGE)
        adb("shell", "am", "start", "-W", "-n", ACTIVITY)
        wait(lambda s: s["boot"] != boot and "main_menu" in s["screens"], "Named-save restart failed")
        tap("Saved games")
        screen("renmodpy_saves")
        tap("Load")
        screen("confirm")
        tap("Yes")
        named = screen("say")
        assert named["history"] == chosen_history and "shared" in named["note_result"]
        assert len(named["records"]) == 1 and named["font_size"] == 1.25 and named["text_cps"] == 0
        capture("named-loaded-dialogue")
        checks.append("Native save-name input, create/confirmed overwrite, process restart and confirmed named-load restore the chosen dialogue")

        home()
        tap("Replay story")
        screen("confirm")
        tap("Yes")
        replayed = wait(lambda s: "say" in s["screens"] and s["history"] == original_history
                        and s["note_result"] is None, "Replay did not reset the story and its choice")
        assert len(replayed["records"]) == 1 and len(replayed["saves"]) == 1 and replayed["quick"]
        assert replayed["font_size"] == 1.25 and replayed["text_cps"] == 0
        assert replayed["clipboard"] == copied_record and replayed["records"][0]["values"] == saved_record["values"]
        capture("replayed-dialogue")
        checks.append("Replay resets story/history/choice state while preserving Records, reading settings, quick and named checkpoints")

        home()
        tap("Saved games")
        screen("renmodpy_saves")
        tap("Delete")
        screen("confirm")
        tap("No")
        retained = wait(lambda s: "confirm" not in s["screens"], "Delete cancellation did not close")
        assert len(retained["saves"]) == 1
        tap("Delete")
        screen("confirm")
        tap("Yes")
        deleted = wait(lambda s: not s["saves"], "Confirmed delete did not remove the checkpoint")
        assert deleted["quick"] and len(deleted["records"]) == 1
        capture("checkpoint-deleted")
        checks.append("Cancelling deletion retains the checkpoint; confirming deletes only the named checkpoint")

        receipt = {"result": "passed", "platform": "Android emulator", "engine": loaded["engine"],
            "api": adb("shell", "getprop", "ro.build.version.sdk").stdout.decode().strip(),
            "abi": adb("shell", "getprop", "ro.product.cpu.abi").stdout.decode().strip(),
            "checks": checks, "physical_device": False, "release": False}
        (output / "passed.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2), flush=True)
    finally:
        (output / "last-state.json").write_text(json.dumps(latest, indent=2) + "\n")
        for path, command in (("logcat.log", ("logcat", "-d")),
                              ("last-screen.png", ("exec-out", "screencap", "-p"))):
            try:
                result = adb(*command, check=False)
                if result.returncode == 0:
                    (output / path).write_bytes(result.stdout)
            except (OSError, subprocess.SubprocessError) as error:
                print(f"Could not collect {path}: {error}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=ROOT / ".renmodpy-build/android-build")
    parser.add_argument("--output", type=Path, default=ROOT / ".renmodpy-build/android-check")
    args = parser.parse_args()
    build = json.loads((args.build / "build.json").read_text())
    run(Path(build["apk"]), args.output)


if __name__ == "__main__":
    main()
