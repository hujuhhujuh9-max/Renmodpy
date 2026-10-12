# Regression driver for the ordinary main menu and the first story interaction.
# This fixture is copied only into the host validation project.

init 900 python:
    import json as _rm_startup_json
    import os as _rm_startup_os
    import sys as _rm_startup_sys
    import types as _rm_startup_types
    from pathlib import Path as _rm_startup_Path

    _rm_startup_probe = _rm_startup_types.ModuleType("renmodpy_startup_probe")
    _rm_startup_sys.modules[_rm_startup_probe.__name__] = _rm_startup_probe
    _rm_startup_probe.phase = _rm_startup_os.environ["RENMODPY_STARTUP_PHASE"]
    _rm_startup_probe.mode = "menu"
    _rm_startup_probe.output = _rm_startup_Path(_rm_startup_os.environ["RENMODPY_CHECK_OUTPUT"])
    config.savedir = _rm_startup_os.environ["RENMODPY_CHECK_SAVEDIR"]
    config.autosave_frequency = None
    config.always_shown_screens.append("renmodpy_startup_driver")

    def _rm_startup_tick():
        mode = _rm_startup_probe.mode
        phase = _rm_startup_probe.phase
        output = _rm_startup_probe.output
        if mode == "menu":
            if not renpy.get_screen("main_menu"):
                return
            assert main_menu
            _rm_startup_probe.mode = "first-line"
            if phase == "save":
                renpy.run(Start("start"))
            else:
                slot = _rm_services.resume_slot() if phase == "resume" else _rm_services.QUICK_SLOT
                assert slot and renpy.can_load(slot)
                renpy.run(FileLoad(slot, slot=True, confirm=False))
            return
        if mode == "first-line":
            if not renpy.get_screen("say"):
                return
            assert not main_menu and _history
            history = [entry.what for entry in _history_list]
            assert len(history) == 1 and "folded note" in history[0]
            if phase == "save":
                (output / "startup-checkpoint.json").write_text(_rm_startup_json.dumps(history))
                _rm_startup_probe.mode = "home"
                renpy.run([Function(_rm_return_home), ShowMenu("renmodpy_home")])
                return
            assert history == _rm_startup_json.loads((output / "startup-checkpoint.json").read_text())
            if phase == "upgrade":
                assert config.version == "0.1.1"
            assert [row["values"]["title"] for row in _rm_services.records().list()] == ["After the first-line save"]
            assert _preferences.font_size == 1.25 and _preferences.text_cps == 0
            assert renpy.screenshot(str(output / ("startup-" + phase + ".png")))
            (output / ("startup-" + phase + "-passed.json")).write_text(_rm_startup_json.dumps({
                "result": "passed", "history": history, "main_menu": main_menu,
                "check": "Ordinary Home load restores the first dialogue after process restart"}, indent=2))
            renpy.quit(status=0, save=False)
        if mode == "home":
            if not renpy.get_screen("renmodpy_home"):
                return
            assert _rm_services.resume_slot()
            _rm_services.save_quick()
            _rm_services.records().create({"title": "After the first-line save"})
            renpy.run(Preference("font size", 1.25))
            renpy.run(Preference("text speed", 0))
            renpy.save_persistent()
            renpy.quit(status=0, save=False)

screen renmodpy_startup_driver():
    zorder 999
    timer 0.7 action Function(_rm_startup_tick) repeat True
