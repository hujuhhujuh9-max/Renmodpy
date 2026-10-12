#!/usr/bin/env python3
"""Install the validation APK and exercise real Android input on a rooted CI emulator."""

import argparse
import json
import hashlib
import re
from pathlib import Path
from media_evidence import inspect_frames
import shlex
import subprocess
import time
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "org.renmodpy.example"
FIXTURE_PACKAGE = "org.renmodpy.validation"
DOCUMENT_PACKAGE = "com.google.android.documentsui"
STATE = f"/data/user/0/{PACKAGE}/files/renmodpy-probe/state.json"
SHARE = f"/data/user/0/{PACKAGE}/files/renmodpy-probe/share.json"
SHARE_ERROR = f"/data/user/0/{PACKAGE}/files/renmodpy-probe/share-error.json"
ACTIVITY = PACKAGE + "/org.renpy.android.PythonSDLActivity"


def adb(*arguments, check=True, timeout=45, data=None):
    return subprocess.run(["adb", *arguments], input=data, capture_output=True, check=check, timeout=timeout)


def run(apk, output, upgrade_apk=None):
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
        origin = current.get("surface_geometry", {}).get("origin", [0, 0])
        x += origin[0]
        y += origin[1]
        return str(round(x)), str(round(y))

    def tap_point(x, y, current, *, wait_update=True):
        adb("shell", "input", "tap", *physical_point(x, y, current))
        if wait_update:
            wait(lambda s: s["boot"] != current["boot"] or s["sequence"] > current["sequence"],
                 "Android observer did not update after the tap")

    def tap(name, *, occurrence=0, scroll=None, wait_update=True):
        signature, stable_since = None, None
        def settled(current):
            nonlocal signature, stable_since
            geometry = current.get("surface_geometry", {})
            bounds = geometry.get("visible_bounds")
            if bounds is None or geometry.get("sequence", 0) < current["sequence"] - 2:
                return False
            # A newly focused default field can precede the IME's first
            # frame by seconds. Require that frame before trusting its origin.
            if current.get("editable_field") is not None and bounds[3] >= current["physical_size"][1]:
                signature, stable_since = None, None
                return False
            current_signature = (tuple(geometry["origin"]), tuple(bounds), current.get("editable_field"))
            if current_signature != signature:
                signature, stable_since = current_signature, time.monotonic()
                return False
            return time.monotonic() - stable_since >= 0.6
        wait(settled, "The native input window did not settle before tapping " + name)
        def matches(current):
            bounds = current.get("surface_geometry", {}).get("visible_bounds", [0, 0, *current.get("physical_size", [720, 1280])])
            result = []
            for button in current.get("buttons", []):
                if button["name"] != name:
                    continue
                x, y, width, height = button["rect"]
                px, py = map(int, physical_point(x + width / 2, y + height / 2, current))
                if bounds[0] <= px < bounds[2] and bounds[1] <= py < bounds[3]:
                    result.append(button)
            return result
        if scroll:
            for _ in range(5):
                current = state()
                if len(matches(current)) > occurrence:
                    break
                left, top, right, bottom = current["surface_geometry"]["visible_bounds"]
                x = round(left + (right - left) * 0.9)
                start, end = (0.8, 0.2) if scroll == "down" else (0.2, 0.8)
                adb("shell", "input", "swipe", str(x), str(round(top + (bottom - top) * start)),
                    str(x), str(round(top + (bottom - top) * end)), "400")
                wait(lambda s: s["sequence"] > current["sequence"], "Scroll observer did not update")
        current = wait(lambda s: len(matches(s)) > occurrence, "No tappable control: " + name)
        sequence = current["sequence"]
        current = wait(lambda s: s.get("surface_geometry", {}).get("sequence", -1) >= sequence,
                       "Native surface geometry did not update before the tap")
        assert "error" not in current["surface_geometry"], current["surface_geometry"]
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

    def native_tap(label, package, evidence):
        android_ui_idle(evidence, package)
        tree = ET.parse(output / (evidence + "-ui.xml"))
        node = next((node for node in tree.iter("node") if label.casefold() in
                    (node.get("text", "").casefold(), node.get("content-desc", "").casefold())), None)
        if node is None:
            raise RuntimeError("No native Android control: " + label)
        x1, y1, x2, y2 = map(int, re.findall(r"-?\d+", node.get("bounds", "")))
        adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))

    def fixture_file(name, data):
        adb("shell", "run-as", FIXTURE_PACKAGE, "mkdir", "-p", "files/documents")
        adb("shell", "run-as", FIXTURE_PACKAGE, "sh", "-c",
            shlex.quote("cat > files/documents/" + name), data=data)

    def fixture_read(name):
        return adb("exec-out", "run-as", FIXTURE_PACKAGE, "cat", "files/" + name).stdout

    def document(action, evidence, *, filename=None, cancel=False):
        before = state()
        tap(action, scroll="up", wait_update=False)
        def picker_open():
            activity = adb("shell", "dumpsys", "activity", "activities").stdout.decode()
            (output / (evidence + "-activity.txt")).write_text(activity)
            return any(DOCUMENT_PACKAGE in line and
                       ("topResumedActivity" in line or "mResumedActivity" in line)
                       for line in activity.splitlines())
        wait_device(picker_open, "Android document picker did not become the resumed activity")
        android_ui_idle(evidence + "-picker", DOCUMENT_PACKAGE)
        capture(evidence + "-picker")
        if cancel:
            adb("shell", "input", "keyevent", "4")
        else:
            native_tap("Show roots", DOCUMENT_PACKAGE, evidence + "-roots-button")
            native_tap("RenModPy fixtures", DOCUMENT_PACKAGE, evidence + "-roots")
            native_tap(filename if filename else "Save", DOCUMENT_PACKAGE, evidence + "-files")
        returned = wait(lambda s: s["boot"] == before["boot"] and "renmodpy_records" in s["screens"]
                        and not s.get("transfer", {}).get("busy", True), "Document callback did not finish on the live Records screen")
        assert returned["draft"] == before["draft"] and returned["editing"] == before["editing"]
        assert returned["history"] == before["history"] and returned["font_size"] == before["font_size"]
        capture(evidence + "-returned")
        return returned

    def replace_field(field, text):
        current = state()
        if current.get("editable_field") != field:
            tap("field:" + field, scroll="up")
        focused = wait(lambda s: s.get("editable_field") == field, "Replacement field did not receive focus")
        adb("shell", "input", "keyevent", "123")
        if focused["input_text"]:
            adb("shell", "input", "keyevent", *(["67"] * len(focused["input_text"])))
        wait(lambda s: s.get("input_text") == "", "Field did not clear")
        if text:
            adb("shell", "input", "text", text.replace(" ", "%s"))
        return wait(lambda s: s.get("input_text") == text, "Replacement text did not reach the form")

    def service(label, operation, *, expected="passed"):
        tap(label)
        result = wait(lambda s: s.get("service_fixture", {}).get("operation") == operation
                      and s["service_fixture"]["result"] != "pending", "Native service callback did not finish")
        assert result["service_fixture"]["result"] == expected, result["service_fixture"]
        assert result["service_fixture"]["owner_thread"]
        return result

    def file_share(evidence):
        before = state()
        sequence = share_report().get("sequence", 0)
        tap("Share backup", scroll="up", wait_update=False)
        wait_device(lambda: share_report().get("sequence", 0) > sequence,
                    "The native file-sharing Intent was not observed")
        report = share_report()
        assert report["ui_thread"] and report["stream"] and report["mime"] == "application/json"
        android_ui_idle(evidence + "-chooser", "com.android.intentresolver")
        capture(evidence + "-chooser")
        native_tap("RenModPy test receiver", "com.android.intentresolver", evidence + "-target")
        def received():
            result = adb("exec-out", "run-as", FIXTURE_PACKAGE, "cat", "files/received.json", check=False)
            try:
                receipt = json.loads(result.stdout)
            except ValueError:
                return False
            (output / (evidence + "-received.json")).write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
            return receipt.get("result") == "passed"
        wait_device(received, "The offline receiver did not read the attachment")
        receipt = json.loads(fixture_read("received.json"))
        assert receipt["scheme"] == "content" and receipt["read_grant"]
        sender_uid = int(adb("shell", "stat", "-c", "%u", f"/data/user/0/{PACKAGE}").stdout)
        assert receipt["uid"] != sender_uid
        payload = json.loads(receipt["text"])
        assert payload["type"] == "renmodpy.records" and payload["records"] == before["records"]
        assert receipt["sha256"] == hashlib.sha256(receipt["text"].encode()).hexdigest()
        android_ui_idle(evidence + "-received", FIXTURE_PACKAGE)
        capture(evidence + "-received")
        adb("shell", "input", "keyevent", "4")
        # Android may launch a chosen receiver in its own task; Back then
        # returns to the launcher. Reopen the sender through its real activity.
        adb("shell", "am", "start", "-W", "-n", ACTIVITY)
        def sender_resumed():
            activity = adb("shell", "dumpsys", "activity", "activities").stdout.decode()
            (output / (evidence + "-returned-activity.txt")).write_text(activity)
            return any(ACTIVITY in line and
                       ("topResumedActivity" in line or "mResumedActivity" in line)
                       for line in activity.splitlines())
        wait_device(sender_resumed, "Android did not foreground the main activity after receiving the attachment")
        returned = wait(lambda s: "renmodpy_records" in s["screens"] and s["sequence"] > before["sequence"],
                        "The offline receiver did not return to Records")
        assert returned["boot"] == before["boot"] and returned["draft"] == before["draft"]
        assert returned["records"] == before["records"] and returned["editable_field"] is None
        capture(evidence + "-returned")

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

    def enter(field, text, *, scroll=None):
        if state().get("editable_field") != field:
            tap("field:" + field, scroll=scroll)
            wait(lambda s: s.get("editable_field") == field, "Field did not receive focus")
        adb("shell", "input", "text", text.replace(" ", "%s"))
        wait(lambda s: s.get("input_text") == text, "Android text input did not reach the form")

    def home():
        field = state().get("editable_field")
        if field is not None:
            tap("field:" + field)
            wait(lambda s: s.get("editable_field") is None, "Home did not dismiss the active input")
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
        adb("install", "-r", str(ROOT / ".renmodpy-build/android-fixtures/fixtures.apk"))
        adb("shell", "pm", "clear", PACKAGE)
        adb("shell", "pm", "clear", FIXTURE_PACKAGE)
        adb("shell", "am", "start", "-W", "-n", ACTIVITY)
        initial = screen("main_menu")
        assert initial["android"], "The APK did not run the Android runtime"
        capture("home")
        tap("Validation tools")
        screen("renmodpy_validation_tools")
        stored = service("Store first fixture", "store-first")
        service("Read first fixture", "read-first")
        service("Touch feedback fixture", "haptic")
        assert stored["worker_events"] and all(event["app_loader"] and not event["ui_thread"] for event in stored["worker_events"])
        feedback = state()["haptic_events"]
        assert feedback and all(event["ui_thread"] for event in feedback)
        private_path = f"/data/user/0/{PACKAGE}/no_backup/renmodpy-secure/" + hashlib.sha256(b"validation.private-note").hexdigest() + ".json"
        encrypted = adb("exec-out", "cat", private_path).stdout
        assert b"First public fixture" not in encrypted
        envelope = json.loads(encrypted)
        assert envelope["version"] == 1 and set(envelope) == {"version", "iv", "ciphertext"}
        (output / "secure-storage.json").write_text(json.dumps({"ciphertext_sha256": hashlib.sha256(encrypted).hexdigest(),
            "plaintext_on_disk": False, "outside_backup": True, "owner_thread": stored["service_fixture"]["owner_thread"]}, indent=2) + "\n")
        checks.append("Android Keystore private text is encrypted outside backup; worker JNI uses the app loader and callbacks run on the engine owner")
        checks.append("Native haptic requests run on Android's UI thread and return a boolean without claiming physical vibration")
        tap("Custom records fixture"); screen("renmodpy_records")
        enter("name", "Separate note", scroll="up")
        enter("details", "Custom fields", scroll="down")
        tap("Add record", scroll="down")
        separate = wait(lambda s: len(s["other_records"]) == 1, "Custom collection did not save")
        assert separate["other_records"][0]["values"] == {"name": "Separate note", "details": "Custom fields"}
        assert separate["records"] == []
        capture("custom-collection")
        home(); tap("Records"); ordinary = screen("renmodpy_records")
        assert ordinary["records"] == [] and ordinary["other_records"] == separate["other_records"]
        checks.append("A real native custom-field form saves into its own private collection without changing ordinary Records")
        home()
        tap("Media room"); screen("renmodpy_example_media")
        wait(lambda s: s.get("media", {}).get("video_texture") and s["media"].get("audio_position") is not None,
             "Native Android audio/video playback did not start")
        media_positions = []
        for index in range(6):
            time.sleep(0.35)
            media_positions.append(state()["media"]["audio_position"])
            capture("media-%d" % index)
        assert all(position is not None for position in media_positions)
        assert len(set(round(position, 2) for position in media_positions)) > 1
        visible_frames = inspect_frames(output / ("media-%d.png" % index) for index in range(6))
        tap("Stop tone")
        wait(lambda s: s.get("media_playing", {}).get("example_tone") is None, "Stop tone did not stop audio")
        tap("Play tone")
        wait(lambda s: s.get("media", {}).get("audio_position") is not None, "Play tone did not restart audio")
        home()
        wait(lambda s: all(value is None for value in s["media_playing"].values()), "Leaving media kept a channel playing")
        (output / "media.json").write_text(json.dumps({"audio_positions": media_positions,
            "visible_frames": visible_frames, "channels_stop_on_exit": True,
            "physical_audio_verified": False}, indent=2) + "\n")
        checks.append("Android native audio playback advances, video visibly decodes both colors and ATL moves; stop/restart and menu exit control playback")
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
        previous_ime = adb("shell", "settings", "get", "secure", "default_input_method").stdout.decode().strip()
        fixture_ime = FIXTURE_PACKAGE + "/.UnicodeIme"
        adb("shell", "ime", "enable", fixture_ime)
        adb("shell", "ime", "set", fixture_ime)
        replace_field("title", "")
        wait(lambda s: s.get("editable_field") == "title", "Unicode test field did not receive focus")
        def ime_ready():
            report = adb("exec-out", "run-as", FIXTURE_PACKAGE, "cat", "files/ime.json", check=False)
            try:
                position = json.loads(report.stdout)
            except ValueError:
                return False
            (output / "ime-ready.json").write_text(json.dumps(position) + "\n")
            return position.get("x", 0) > 0 and position.get("y", 0) > 0
        wait_device(ime_ready, "The composition keyboard did not open")
        before_keyboard = state()["sequence"]
        wait(lambda s: s["surface_geometry"]["sequence"] > before_keyboard
             and 0 < s["physical_size"][1] - s["surface_geometry"]["visible_bounds"][3] <= 200,
             "The composing keyboard did not finish showing")
        android_ui_idle("unicode-ime-ready", PACKAGE)
        capture("unicode-ime-ready")
        ime = json.loads((output / "ime-ready.json").read_text())
        assert ime["ui_thread"]
        adb("shell", "input", "tap", str(ime["x"]), str(ime["y"]))
        composed = wait(lambda s: s.get("input_text") == "café", "Native IME composition did not reach the form")
        assert composed["records"] == [] and composed["history"] == original_history
        composition = json.loads(fixture_read("composition.json"))
        assert all(composition.values()), composition
        (output / "ime-composition.json").write_text(json.dumps(composition, indent=2) + "\n")
        capture("unicode-ime-composition")
        adb("shell", "ime", "set", previous_ime)
        tap("field:title")
        wait(lambda s: s.get("editable_field") is None, "Composition input did not deactivate")
        tap("Cancel edit", scroll="up")
        wait(lambda s: not any(s.get("draft", {}).values()), "Cancelling composition did not clear the unsaved draft")
        checks.append("A native InputConnection composes and commits café into the actual form; cancelling preserves saved Records and the waiting story")
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
        enter("title", "Keep draft", scroll="up")
        tap("field:title")
        wait(lambda s: s.get("editable_field") is None, "Record input stayed active")
        shared = share("Share record", copied_record, "renmodpy_records", "record-share", scroll="down")
        assert shared["draft"] == {"title": "Keep draft", "body": ""}
        checks.append("Real Android text choosers receive Unicode/multiline history and saved Records on the UI thread; dismissal preserves the draft, story, preferences and saves")
        checks.append("Native history/record copy and Unicode/multiline paste use the platform clipboard; rejected title paste preserves the draft")
        cancelled = document("Import backup", "import-cancel", cancel=True)
        assert cancelled["records"] == shared["records"] and "cancelled" in cancelled["form_message"].lower()
        exported = document("Export backup", "export-backup")
        assert "exported" in exported["form_message"].lower()
        export_text = fixture_read("documents/records.json").decode("utf-8")
        export_data = json.loads(export_text)
        assert export_data["records"] == exported["records"]
        (output / "export-backup.json").write_text(export_text)
        file_share("file-share")
        fixture_file("malformed.json", b"not a JSON backup")
        malformed = document("Import backup", "import-malformed", filename="malformed.json")
        assert malformed["records"] == shared["records"] and malformed["transfer"]["preview"] is None
        imported_rows = [{"id": saved_record["id"], "values": {"title": "Imported title", "body": original_history[-1]}},
                         {"id": "a" * 32, "values": {"title": "Added by backup", "body": "Café Ω", "extra": "Hidden backup field"}}]
        fixture_file("backup.json", json.dumps({"type": "renmodpy.records", "version": 1,
                     "records": imported_rows}, ensure_ascii=False).encode())
        previewed = document("Import backup", "import-preview", filename="backup.json")
        assert previewed["records"] == shared["records"] and previewed["transfer"]["preview"]["new"] == 1
        assert previewed["transfer"]["preview"]["updated"] == 1
        tap("Cancel import", scroll="up")
        wait(lambda s: s.get("transfer", {}).get("preview") is None, "Cancelling preview did not clear it")
        document("Import backup", "import-confirm", filename="backup.json")
        tap("Import these records", scroll="up")
        imported = wait(lambda s: len(s["records"]) == 2, "Confirmed import did not merge the backup")
        assert imported["draft"] == {"title": "Keep draft", "body": ""}
        assert imported["records"][1]["values"]["extra"] == "Hidden backup field"
        (output / "import-confirmed.json").write_text(json.dumps(imported, indent=2, ensure_ascii=False) + "\n")
        tap("Title A–Z", scroll="down")
        sorted_records = wait(lambda s: s.get("displayed_record_ids") == ["a" * 32, saved_record["id"]],
                              "Sorting did not change the visible record order")
        assert sorted_records["records"] == imported["records"] and sorted_records["draft"] == imported["draft"]
        capture("records-sorted")
        tap("Saved order", scroll="up")
        wait(lambda s: s.get("displayed_record_ids") == [saved_record["id"], "a" * 32], "Saved order did not restore")
        tap("Delete", occurrence=1, scroll="down")
        screen("confirm"); tap("No")
        wait(lambda s: "confirm" not in s["screens"], "Record delete cancellation did not close")
        assert len(state()["records"]) == 2
        tap("Delete", occurrence=1, scroll="down")
        screen("confirm"); tap("Yes")
        wait(lambda s: len(s["records"]) == 1, "Confirmed record deletion did not remove the imported row")
        tap("Cancel edit", scroll="up")
        wait(lambda s: not any(s.get("draft", {}).values()), "Draft cancellation did not clear fields")
        tap("Edit", scroll="down")
        wait(lambda s: s.get("editing") == saved_record["id"], "Record editing did not open")
        replace_field("title", "Discarded edit")
        tap("field:title"); wait(lambda s: s.get("editable_field") is None, "Input did not deactivate")
        tap("Cancel edit", scroll="up")
        wait(lambda s: s.get("editing") is None, "Cancel edit did not close")
        assert state()["records"][0]["values"]["title"] == "Imported title"
        tap("Edit", scroll="down")
        wait(lambda s: s.get("editing") == saved_record["id"], "Record editing did not reopen")
        replace_field("title", "Emulator note")
        tap("field:title"); wait(lambda s: s.get("editable_field") is None, "Input did not deactivate")
        tap("Save changes", scroll="up")
        wait(lambda s: s["records"][0]["values"] == saved_record["values"], "Record edit did not restore the original fixture")
        checks.append("Scoped document export/import, cancellation, malformed JSON and confirmed backup merge preserve the draft; another UID reads the granted attachment offline")
        checks.append("Real Android edit/cancel/save and cancelled/confirmed record deletion retain the intended saved data")
        home()
        tap("Validation tools"); screen("renmodpy_validation_tools")
        service("Store newer fixture", "store-newer")
        service("Read newer fixture", "read-newer")
        encrypted_newer = adb("exec-out", "cat", private_path).stdout
        damaged = json.loads(encrypted_newer)
        damaged["ciphertext"] = ("A" if damaged["ciphertext"][0] != "A" else "B") + damaged["ciphertext"][1:]
        damaged_bytes = json.dumps(damaged).encode()
        adb("shell", "sh", "-c", shlex.quote("cat > " + private_path), data=damaged_bytes)
        failed_storage = service("Read newer fixture", "read-newer", expected="failed")
        assert failed_storage["service_fixture"]["error"]
        assert adb("exec-out", "cat", private_path).stdout == damaged_bytes
        adb("shell", "sh", "-c", shlex.quote("cat > " + private_path), data=encrypted_newer)
        service("Read newer fixture", "read-newer")
        checks.append("Authenticated private storage rejects tampered ciphertext without deleting it or replacing the key")
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
        home(); tap("Validation tools"); screen("renmodpy_validation_tools")
        service("Read newer fixture", "read-newer")
        home(); tap("Resume story"); restored = screen("say")
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
        home(); tap("Validation tools"); screen("renmodpy_validation_tools")
        service("Read newer fixture", "read-newer")
        home(); tap("Resume story"); loaded = screen("say")

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
        home(); tap("Validation tools"); screen("renmodpy_validation_tools")
        service("Read newer fixture", "read-newer")

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

        home()
        before_upgrade = state()
        if upgrade_apk is not None:
            adb("install", "-r", str(upgrade_apk), timeout=180)
            adb("shell", "am", "start", "-W", "-n", ACTIVITY)
            upgraded = wait(lambda s: s["boot"] != before_upgrade["boot"] and "main_menu" in s["screens"]
                            and s.get("app_version") == "0.1.1", "Same-key APK upgrade did not start the new version")
            for key in ("records", "other_records", "font_size", "text_cps", "quick", "saves"):
                assert upgraded[key] == before_upgrade[key], "APK upgrade changed " + key
            tap("Validation tools"); screen("renmodpy_validation_tools")
            service("Read newer fixture", "read-newer")
            assert adb("exec-out", "cat", private_path).stdout == encrypted_newer
            home(); tap("Resume story"); upgraded_story = screen("say")
            assert upgraded_story["history"] == original_history
            capture("same-key-upgraded-story")
            checks.append("A signed same-key APK upgrade starts the new version while keeping Records, preferences, quick saves, story Resume and the encrypted Keystore entry")
        home(); tap("Validation tools"); screen("renmodpy_validation_tools")
        service("Read newer fixture", "read-newer")
        service("Delete private fixture", "delete")
        service("Read missing fixture", "read-missing")
        assert adb("shell", "test", "-f", private_path, check=False).returncode != 0
        checks.append("Private storage survives process restart, older quick-load and replay; explicit deletion removes the entry and subsequent reads return missing")

        home(); tap("Records"); screen("renmodpy_records")
        enter("title", "Profile draft", scroll="up")
        tap("field:title")
        wait(lambda s: s.get("editable_field") is None, "Profile input did not deactivate")
        profile_state = state()
        profiles = []
        for width, height, density in ((480, 800, 160), (1080, 2400, 320), (720, 1280, 160)):
            adb("shell", "wm", "size", f"{width}x{height}")
            adb("shell", "wm", "density", str(density))
            resized = wait(lambda s: s["physical_size"] == [width, height] and "renmodpy_records" in s["screens"],
                           "Screen-size change did not retain the live Records screen")
            assert resized["draft"] == profile_state["draft"] and resized["records"] == profile_state["records"]
            assert resized["history"] == profile_state["history"] and resized["font_size"] == 1.25
            capture(f"profile-{width}-{height}")
            tap("field:title", scroll="up")
            wait(lambda s: s.get("editable_field") == "title", "Scaled form control did not receive focus")
            tap("field:title")
            wait(lambda s: s.get("editable_field") is None, "Scaled form control did not deactivate")
            profiles.append({"size": [width, height], "density": density, "draft_preserved": True, "input_tapped": True})
        adb("shell", "settings", "put", "system", "accelerometer_rotation", "0")
        adb("shell", "settings", "put", "system", "user_rotation", "1")
        rotated = wait(lambda s: s.get("device_orientation") == 1 and "renmodpy_records" in s["screens"],
                       "The portrait application did not retain its declared orientation")
        assert rotated["draft"] == profile_state["draft"] and rotated["records"] == profile_state["records"]
        capture("portrait-after-rotation-request")
        adb("shell", "settings", "put", "system", "user_rotation", "0")
        (output / "screen-profiles.json").write_text(json.dumps({"profiles": profiles,
            "rotation_requested": "landscape", "application_orientation": "portrait", "live_state_preserved": True}, indent=2) + "\n")
        tap("Cancel edit", scroll="up")
        wait(lambda s: not any(s.get("draft", {}).values()), "Profile draft did not cancel")
        checks.append("Compact and tall emulator sizes/densities retain the live draft, saved data and reading settings with tappable inputs; a landscape request respects the portrait app")

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
    run(Path(build["apk"]), args.output, Path(build["upgrade_apk"]) if build.get("upgrade_apk") else None)


if __name__ == "__main__":
    main()
