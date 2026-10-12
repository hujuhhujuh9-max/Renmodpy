# Regression driver for mobile recovery policy using the real native engine.
# Only copied into disposable host validation projects.

init 900 python:
    import json as _rm_lifecycle_json
    import os as _rm_lifecycle_os
    import sys as _rm_lifecycle_sys
    import types as _rm_lifecycle_types
    from pathlib import Path as _rm_lifecycle_Path

    _rm_lifecycle_probe = _rm_lifecycle_types.ModuleType("renmodpy_lifecycle_probe")
    _rm_lifecycle_sys.modules[_rm_lifecycle_probe.__name__] = _rm_lifecycle_probe
    _rm_lifecycle_probe.phase = _rm_lifecycle_os.environ["RENMODPY_LIFECYCLE_PHASE"]
    _rm_lifecycle_probe.mode = "menu"
    _rm_lifecycle_probe.output = _rm_lifecycle_Path(_rm_lifecycle_os.environ["RENMODPY_CHECK_OUTPUT"])
    config.savedir = _rm_lifecycle_os.environ["RENMODPY_CHECK_SAVEDIR"]
    config.autosave_frequency = None
    config.always_shown_screens.append("renmodpy_lifecycle_driver")

    def _rm_lifecycle_tick():
        mode = _rm_lifecycle_probe.mode
        phase = _rm_lifecycle_probe.phase
        output = _rm_lifecycle_probe.output
        if mode == "menu":
            if not renpy.get_screen("main_menu"):
                return
            assert main_menu
            if phase == "save-choice":
                _rm_lifecycle_probe.mode = "first-line"
                renpy.run(Start("start"))
                return
            # A cold process opens Home. Switching away and back before
            # Resume must not discard the newer background checkpoint.
            slot = _rm_services.resume_slot()
            assert slot == "_reload-1", "Home did not offer the newest background checkpoint"
            metadata = renpy.slot_json(slot)
            renpy.display.interface.mobile_save()
            renpy.display.interface.mobile_unlink()
            assert renpy.can_load(slot), "Switching apps from cold Home discarded the recovery checkpoint"
            assert renpy.slot_json(slot) == metadata
            assert _rm_services.resume_slot() == slot
            _rm_lifecycle_probe.mode = "choice" if phase == "resume-choice" else "dialogue"
            renpy.run(FileLoad(slot, slot=True, confirm=False))
            return
        if mode == "first-line":
            if not renpy.get_screen("say"):
                return
            assert not main_menu and _history
            history = [entry.what for entry in _history_list]
            assert len(history) == 1 and "folded note" in history[0]
            (output / "lifecycle-first-line.json").write_text(_rm_lifecycle_json.dumps(history))
            # Both explicit checkpoints predate the waiting choice.
            _rm_services.save_resume()
            _rm_services.save_quick()
            _rm_lifecycle_probe.mode = "choice"
            return True
        if mode == "choice":
            if not renpy.get_screen("choice"):
                return
            assert not main_menu and _history
            history = [entry.what for entry in _history_list]
            assert history == _rm_lifecycle_json.loads((output / "lifecycle-first-line.json").read_text())
            assert getattr(renpy.store, "note_result", None) is None
            assert renpy.screenshot(str(output / ("lifecycle-" + phase + ".png")))
            if phase == "save-choice":
                renpy.display.interface.mobile_save()
                assert _rm_services.resume_slot() == "_reload-1"
                # This application data and reading preference are newer
                # than every story snapshot, including the recovery save.
                _rm_services.records().create({"title": "After background save", "body": history[0]})
                renpy.run(Preference("font size", 1.25))
                renpy.run(Preference("text speed", 0))
                renpy.save_persistent()
                renpy.quit(status=0, save=False)
            assert phase == "resume-choice"
            _rm_lifecycle_probe.mode = "dialogue"
            return renpy.run(renpy.get_screen("choice").scope["items"][0].action)
        if mode == "dialogue":
            if not renpy.get_screen("say"):
                return
            assert not main_menu and _history
            history = [entry.what for entry in _history_list]
            result = getattr(renpy.store, "note_result", None)
            assert len(history) == 2 and "kept a copy" in result
            assert [row["values"]["title"] for row in _rm_services.records().list()] == ["After background save"]
            assert _preferences.font_size == 1.25 and _preferences.text_cps == 0
            assert _rm_services.quick_available()
            if phase == "resume-choice":
                (output / "lifecycle-dialogue.json").write_text(_rm_lifecycle_json.dumps({
                    "history": history, "note_result": result}))
                renpy.display.interface.mobile_save()
                assert _rm_services.resume_slot() == "_reload-1"
                renpy.quit(status=0, save=False)
            assert phase == "resume-dialogue"
            expected = _rm_lifecycle_json.loads((output / "lifecycle-dialogue.json").read_text())
            assert {"history": history, "note_result": result} == expected
            assert renpy.screenshot(str(output / "lifecycle-resumed-dialogue.png"))
            # A normal foreground return to this live story still removes
            # its temporary background save; the live session is retained.
            renpy.display.interface.mobile_save()
            renpy.display.interface.mobile_unlink()
            assert not renpy.can_load("_reload-1")
            assert [entry.what for entry in _history_list] == history and note_result == result
            (output / "lifecycle-passed.json").write_text(_rm_lifecycle_json.dumps({
                "result": "passed", "checks": [
                    "cold Home app switch keeps the latest background checkpoint",
                    "fresh-process recovery restores a waiting choice and later chosen dialogue",
                    "recovery keeps newer Records and reading preferences",
                    "live foreground cleanup keeps the story session and quick save"]}, indent=2))
            renpy.quit(status=0, save=False)

screen renmodpy_lifecycle_driver():
    zorder 999
    timer 0.7 action Function(_rm_lifecycle_tick) repeat True
