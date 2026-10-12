#!/usr/bin/env python3
"""Install the validation APK and exercise real Android input on a rooted CI emulator."""

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "org.renmodpy.example"
STATE = f"/data/user/0/{PACKAGE}/files/renmodpy-probe/state.json"
SHARE = f"/data/user/0/{PACKAGE}/files/renmodpy-probe/share.json"
SHARE_ERROR = f"/data/user/0/{PACKAGE}/files/renmodpy-probe/share-error.json"
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

    def wait_device(predicate, message, timeout=60):
        # The observer intentionally stops when SDL is suspended. Wait for
        # Android/device state rather than an update from the paused engine.
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.4)
        raise RuntimeError(message)

    def recovery_file(current):
        return shlex.quote(current["recovery_file"])

    def background(current):
        previous = adb("exec-out", "cat", recovery_file(current), check=False).stdout
        adb("shell", "input", "keyevent", "3")
        def stopped():
            activity = adb("shell", "dumpsys", "activity", "-p", PACKAGE, "activities").stdout
            (output / "background-activity.txt").write_bytes(activity)
            return b"state=STOPPED" in activity
        wait_device(stopped, "Android did not stop the background activity")
        if not current["main_menu"]:
            wait_device(lambda: adb("exec-out", "cat", recovery_file(current), check=False).stdout not in (b"", previous),
                        "SDL did not finish writing its background checkpoint")

    def foreground(current, name):
        adb("shell", "am", "start", "-W", "-n", ACTIVITY)
        return wait(lambda s: s["boot"] == current["boot"] and s["sequence"] > current["sequence"]
                    and name in s["screens"], "Android did not restore the live " + name + " screen")

    def cold_background(current):
        background(current)
        adb("shell", "am", "kill", PACKAGE)
        wait_device(lambda: not adb("shell", "pidof", PACKAGE, check=False).stdout.strip(),
                    "Android did not kill the stopped app process")
        adb("shell", "am", "start", "-W", "-n", ACTIVITY)
        return wait(lambda s: s["boot"] != current["boot"] and "main_menu" in s["screens"],
                    "Background process recovery did not reopen Home")

    def capture(name):
        (output / (name + ".png")).write_bytes(adb("exec-out", "screencap", "-p").stdout)

    def physical_point(x, y, current):
        physical_width, physical_height = current["physical_size"]
        virtual_width, virtual_height = current["virtual_size"]
        scale = min(physical_width / virtual_width, physical_height / virtual_height)
        x = (physical_width - virtual_width * scale) / 2 + x * scale
        y = (physical_height - virtual_height * scale) / 2 + y * scale
        return str(round(x)), str(round(y))

    def tap_point(x, y, current, *, wait_update=True):
        adb("shell", "input", "tap", *physical_point(x, y, current))
        if wait_update:
            wait(lambda s: s["boot"] != current["boot"] or s["sequence"] > current["sequence"],
                 "Android observer did not update after the tap")

    def tap(name, *, occurrence=0, scroll=None, wait_update=True):
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
        tap_point(x + width / 2, y + height / 2, current, wait_update=wait_update)

    def share_report(path=SHARE):
        result = adb("exec-out", "cat", path, check=False)
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except ValueError:
                pass
        return {}

    def android_ui_idle(evidence, package):
        # The resumed-activity dump can precede the chooser's first frame.
        # UIAutomator waits for the actual Android view hierarchy to be idle.
        path = "/sdcard/renmodpy-ui.xml"
        adb("shell", "rm", "-f", path)
        deadline = time.monotonic() + 60
        attempts = []
        while time.monotonic() < deadline:
            result = adb("shell", "uiautomator", "dump", "--compressed", path, check=False)
            hierarchy = adb("exec-out", "cat", path, check=False).stdout
            try:
                tree = ET.fromstring(hierarchy)
                ready = any(node.get("package") == package for node in tree.iter("node"))
            except ET.ParseError:
                ready = False
            # UIAutomator can exit 0 after its idle timeout without a file;
            # require a real hierarchy from the expected foreground package.
            attempts.append({"returncode": result.returncode, "stdout": result.stdout.decode(errors="replace"),
                             "stderr": result.stderr.decode(errors="replace"), "ready": ready})
            (output / (evidence + "-capture.json")).write_text(json.dumps(attempts, indent=2) + "\n")
            if ready:
                (output / (evidence + "-ui.xml")).write_bytes(hierarchy)
                return
            time.sleep(0.4)
        raise RuntimeError("Android view capture did not become ready for " + package)

    def share(name, text, screen_name, evidence, *, scroll=None):
        before = state()
        previous = share_report().get("sequence", 0)
        # SDL may suspend before its next observer tick when the chooser opens.
        tap(name, scroll=scroll, wait_update=False)
        def chooser_open():
            state()
            error = share_report(SHARE_ERROR)
            if error.get("boot") == before["boot"]:
                (output / "share-error.json").write_text(json.dumps(error, indent=2, ensure_ascii=False) + "\n")
                raise RuntimeError("Native share dispatch failed: " + error["traceback"])
            activity = adb("shell", "dumpsys", "activity", "activities").stdout.decode()
            (output / (evidence + "-activity.txt")).write_text(activity)
            return any("ChooserActivity" in line and
                       ("topResumedActivity" in line or "mResumedActivity" in line)
                       for line in activity.splitlines())
        wait_device(chooser_open, "Android's share chooser did not become the resumed activity")
        wait_device(lambda: share_report().get("sequence", 0) > previous,
                    "The requested Android Intent was not observed")
        report = share_report()
        (output / (evidence + "-intent.json")).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        assert report["boot"] == before["boot"] and report["ui_thread"]
        assert report["chooser_action"] == "android.intent.action.CHOOSER"
        assert report["action"] == "android.intent.action.SEND" and report["mime"] == "text/plain"
        assert report["text"] == text, "Android text extra did not match: " + repr(report)
        assert report["subject"] is None and not report["stream"]
        android_ui_idle(evidence + "-chooser", "com.android.intentresolver")
        capture(evidence + "-chooser")
        paused = state()
        adb("shell", "input", "keyevent", "4")
        def app_resumed():
            activity = adb("shell", "dumpsys", "activity", "activities").stdout.decode()
            (output / (evidence + "-returned-activity.txt")).write_text(activity)
            return any(ACTIVITY in line and
                       ("topResumedActivity" in line or "mResumedActivity" in line)
                       for line in activity.splitlines())
        wait_device(app_resumed, "Android did not resume RenModPy after dismissing the chooser")
        returned = wait(lambda s: s["boot"] == before["boot"] and s["sequence"] > paused["sequence"]
                        and screen_name in s["screens"] and s.get("ui_callbacks") == 0,
                        "Dismissing the share chooser did not restore the live app screen")
        for key in ("history", "note_result", "records", "saves", "quick", "font_size", "text_cps", "draft", "editing"):
            assert returned.get(key) == before.get(key), "Sharing changed " + key
        if screen_name == "renmodpy_records":
            assert returned.get("editable_field") is None, "Sharing reactivated a Records input"
        android_ui_idle(evidence + "-returned", PACKAGE)
        capture(evidence + "-returned")
        return returned

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
        if "choice" not in state()["screens"]:
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
        for name in ("window_animation_scale", "transition_animation_scale", "animator_duration_scale"):
            adb("shell", "settings", "put", "global", name, "0")
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
        share("Share line", original_history[-1], "renmodpy_history", "history-share")
        home()
        tap("Records")
        screen("renmodpy_records")
        enter("title", "Emulator note")
        draft = state()
        assert draft["editable_field"] == "title" and draft["records"] == []
        background(draft)
        returned = foreground(draft, "renmodpy_records")
        assert returned["draft"] == draft["draft"] and returned["editing"] == draft["editing"]
        assert returned["history"] == original_history and returned["records"] == []
        assert returned["font_size"] == 1.25 and returned["text_cps"] == 0
        wait_device(lambda: adb("shell", "test", "-f", recovery_file(returned), check=False).returncode != 0,
                    "Live foreground return did not clear its temporary checkpoint")
        capture("background-restored-draft")
        checks.append("Android app switching preserves the live Records draft, waiting story and reading settings without saving a record")
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
        # Keep an unsaved form draft while sharing the saved row. Its export
        # must use saved values, and Back from Android must keep that draft.
        tap("field:title", scroll="up")
        enter("title", "Keep draft")
        tap("field:title")
        wait(lambda s: s.get("editable_field") is None, "Record input stayed active")
        shared = share("Share record", copied_record, "renmodpy_records", "record-share", scroll="down")
        assert shared["draft"] == {"title": "Keep draft", "body": ""}
        checks.append("Real Android text choosers receive Unicode/multiline history and saved Records on the UI thread; dismissal preserves the draft, story, preferences and saves")
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
        # The waiting choice is newer than the explicit Home/quick saves.
        # Exercise native background saving without using the app's Home.
        tap_point(360, 1000, restored)
        pending_choice = screen("choice")
        assert pending_choice["note_result"] is None
        cold_home = cold_background(pending_choice)
        assert cold_home["resume"] == "_reload-1"
        recovery = adb("exec-out", "cat", recovery_file(cold_home)).stdout
        # A fresh Home may be backgrounded before the user clicks Resume.
        # Its foreground cleanup must not throw away the pending recovery.
        background(cold_home)
        returned_home = foreground(cold_home, "main_menu")
        assert returned_home["resume"] == "_reload-1"
        assert adb("exec-out", "cat", recovery_file(returned_home)).stdout == recovery
        capture("background-recovery-home")
        tap("Resume story")
        recovered_choice = screen("choice")
        assert recovered_choice["history"] == pending_choice["history"] and recovered_choice["note_result"] is None
        assert recovered_choice["records"][0]["values"] == saved_record["values"]
        assert recovered_choice["font_size"] == 1.25 and recovered_choice["text_cps"] == 0
        capture("background-choice")
        checks.append("A background process kill recovers the waiting choice; switching apps from cold Home keeps that latest checkpoint")
        chosen = choose("Keep a copy")
        assert chosen["history"] != original_history and "kept a copy" in chosen["note_result"]
        cold_home = cold_background(chosen)
        assert cold_home["resume"] == "_reload-1"
        tap("Resume story")
        recovered_dialogue = screen("say")
        assert recovered_dialogue["history"] == chosen["history"] and recovered_dialogue["note_result"] == chosen["note_result"]
        assert recovered_dialogue["records"][0]["values"] == saved_record["values"]
        assert recovered_dialogue["font_size"] == 1.25 and recovered_dialogue["text_cps"] == 0
        capture("background-dialogue")
        checks.append("Native background recovery restores dialogue and choices newer than the explicit saves while keeping Records and reading settings")
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
