# Installed only in a disposable test project by check_native.py.

init 900 python:
    import json as _rm_check_json
    import os as _rm_check_os
    import sys as _rm_check_sys
    import types as _rm_check_types
    from pathlib import Path as _rm_check_Path
    from renpy.renmodpy.tactics import Cell as _rm_check_Cell
    import renpy.pygame as _rm_check_pygame

    # Transient driver state must not itself be restored by a story load.
    _rm_check_probe = _rm_check_types.ModuleType("renmodpy_native_probe")
    _rm_check_sys.modules[_rm_check_probe.__name__] = _rm_check_probe
    _rm_check_probe.output = _rm_check_Path(_rm_check_os.environ["RENMODPY_CHECK_OUTPUT"])
    _rm_check_probe.phase = _rm_check_os.environ.get("RENMODPY_CHECK_PHASE", "save")
    _rm_check_probe.mode = "home"
    config.savedir = _rm_check_os.environ["RENMODPY_CHECK_SAVEDIR"]
    config.label_overrides["start"] = ("renmodpy_check_restarted" if
        _rm_check_probe.phase == "replay" else "renmodpy_check_start")
    config.performance_test = False
    config.check_conflicting_properties = True
    config.autosave_frequency = None
    config.always_shown_screens.append("renmodpy_check_driver")


    def _rm_check_write(filename, value):
        (_rm_check_probe.output / filename).write_text(_rm_check_json.dumps(value, indent=2))

    def _rm_check_capture(name):
        assert renpy.screenshot(str(_rm_check_probe.output / (name + ".png")))

    def _rm_check_savedirs(name):
        _rm_check_write(name + ".json", [{"directory": location.directory,
            "active": location.active, "slots": location.list(),
            "files": sorted(path.name for path in _rm_check_Path(location.directory).iterdir())}
            for location in renpy.loadsave.location.locations])

    def _rm_check_list(screen, identifier, variable):
        rows = renpy.get_screen_variable(variable, screen=screen)
        if variable == "snapshot":
            rows = rows["records"]
        assert len(rows) == 1, "Expected one populated list row"
        viewport = renpy.get_displayable(screen, identifier)
        assert viewport.width > 500 and viewport.height > 200, "List was laid out offscreen"

    def _rm_check_after_load():
        _rm_check_savedirs("after-load-" + _rm_check_probe.phase)
        checkpoint = _rm_check_json.loads((_rm_check_probe.output / "checkpoint.json").read_text())
        actual = _rm_check_json.loads(_rm_check_json.dumps(_renmodpy_board.snapshot()))
        assert actual == checkpoint["board"], "Board/camera did not restore"
        assert renmodpy_check_counter == 1, "Story variables did not restore"
        assert [r["values"]["title"] for r in _rm_services.records().list()] == [
            "Before save", "Newer {application} [data]"], "Loading rolled records back"
        assert _preferences.font_size == 1.25 and _preferences.text_cps == 0, "Load rewound reading settings"
        assert any("This dialogue waits" in (entry.what or "") for entry in _history_list)
        _rm_check_probe.mode = ("replay-home" if _rm_check_probe.phase == "replay" else "reloaded-tactics")

    config.after_load_callbacks.append(_rm_check_after_load)
    config.before_load_callbacks.append(lambda: _rm_check_savedirs("before-load-" + _rm_check_probe.phase))
    config.start_callbacks.append(lambda: _rm_check_savedirs("start-" + _rm_check_probe.phase))

    def _rm_check_tick():
        mode = _rm_check_probe.mode
        if mode in ("home", "records", "saves"):
            if not renpy.get_screen("renmodpy_" + mode):
                return None
            _rm_check_capture(mode)
            if mode == "records":
                _rm_check_list("renmodpy_records", "records_list", "snapshot")
                snapshot = renpy.get_screen_variable("snapshot", screen="renmodpy_records")
                form = renpy.get_screen_variable("form", screen="renmodpy_records")
                inputs = renpy.get_screen_variable("input_values", screen="renmodpy_records")
                identifier = snapshot["records"][0]["id"]
                _rm_edit_record(form, snapshot, identifier)
                assert inputs["title"].get_text() == "Before save"
                _rm_copy_record(snapshot["records"][0]["values"], form.fields, form)
                assert _rm_services.clipboard_text() == "Before save\n\nA lighthouse note"
                draft = dict(form.values)
                _rm_share_record(snapshot["records"][0]["values"], form.fields, form)
                assert "available on Android" in form.message
                assert dict(form.values) == draft and form.editing_id == identifier
                assert not form.needs_reload
                _rm_services.copy_text("Edited note\nwith Unicode Blåbær")
                _rm_paste_record(form, "title")
                assert inputs["title"].get_text() == "Before save", "Rejected paste replaced a draft"
                inputs["body"].set_text("")
                _rm_paste_record(form, "body")
                assert inputs["body"].get_text() == "Edited note\nwith Unicode Blåbær"
                temporary = _rm_services.records().create({"title": "Concurrent change"})
                _rm_submit_record(form, "records", _rm_services.records().snapshot()["revision"])
                assert form.needs_reload and form.values["body"].startswith("Edited note")
                _rm_services.records().delete(temporary)
                _rm_reload_records(form, "records")
                assert not form.needs_reload and form.editing_id == identifier
                transfer = renpy.get_screen_variable("transfer", screen="renmodpy_records")
                original_picker = _rm_services.pick_text
                imported_draft = dict(form.values)
                try:
                    _rm_services.pick_text = lambda done, **kwargs: done(_rm_transfers.dump_records(
                        _rm_services.records().snapshot()), None)
                    _rm_import_records(form, "records", transfer)
                    assert transfer["preview"]["unchanged"] == 1 and not transfer["busy"]
                    assert dict(form.values) == imported_draft and form.editing_id == identifier
                    _rm_apply_import(form, "records", transfer)
                    assert form.needs_reload and dict(form.values) == imported_draft
                    assert _rm_services.records().list()[0]["values"]["extra"] == "Keep outside the visible schema"
                    _rm_reload_records(form, "records")
                    assert not form.needs_reload and dict(form.values) == imported_draft
                finally:
                    _rm_services.pick_text = original_picker
                _rm_check_probe.sort_draft = dict(form.values)
                _rm_check_probe.sort_temporary = _rm_services.records().create({"title": "alpha Ω"})
                _rm_check_probe.sort_rows = _rm_services.records().list()
                renpy.set_screen_variable("sort_mode", "title", screen="renmodpy_records")
                _rm_check_probe.mode = "records-sorted"
                return None
            return True
        if mode == "records-sorted":
            rows = renpy.get_screen_variable("displayed_records", screen="renmodpy_records")
            assert [row["id"] for row in rows] == [row["id"] for row in reversed(_rm_check_probe.sort_rows)]
            assert _rm_services.records().list() == _rm_check_probe.sort_rows
            form = renpy.get_screen_variable("form", screen="renmodpy_records")
            assert dict(form.values) == _rm_check_probe.sort_draft
            renpy.set_screen_variable("sort_mode", "saved", screen="renmodpy_records")
            _rm_check_probe.mode = "records-saved-order"
            return None
        if mode == "records-saved-order":
            rows = renpy.get_screen_variable("displayed_records", screen="renmodpy_records")
            assert rows == _rm_check_probe.sort_rows
            form = renpy.get_screen_variable("form", screen="renmodpy_records")
            assert dict(form.values) == _rm_check_probe.sort_draft
            _rm_services.records().delete(_rm_check_probe.sort_temporary)
            _rm_reload_records(form, "records")
            # Evaluate the Android-only controls on the real native screen
            # without changing the host engine's platform or JNI backend.
            renpy.get_screen("renmodpy_records").scope["renpy"] = _rm_check_types.SimpleNamespace(android=True)
            _rm_check_probe.mode = "records-android"
            return None
        if mode == "records-android":
            form = renpy.get_screen_variable("form", screen="renmodpy_records")
            inputs = renpy.get_screen_variable("input_values", screen="renmodpy_records")
            identifier = form.editing_id
            _rm_check_probe.sharing_draft = dict(form.values)
            _rm_check_probe.sharing_identifier = identifier
            renpy.run(inputs["body"].Enable())
            button = renpy.get_displayable("renmodpy_records", "record_share_" + identifier, base=True)
            renpy.run(button.action)
            _rm_check_probe.mode = "records-android-return"
            return None
        if mode == "records-android-return":
            form = renpy.get_screen_variable("form", screen="renmodpy_records")
            assert not renpy.get_editable_input_value()[1], "Sharing reactivated the default form input"
            assert "available on Android" in form.message
            assert dict(form.values) == _rm_check_probe.sharing_draft
            assert form.editing_id == _rm_check_probe.sharing_identifier and not form.needs_reload
            del renpy.get_screen("renmodpy_records").scope["renpy"]
            _rm_check_probe.link_form = form
            _rm_check_probe.link_history = list(_history_list)
            _rm_check_probe.mode = "records-link"
            _rm_open_record_link(_rm_check_probe.sharing_identifier)
            return None
        if mode == "records-link":
            assert renpy.get_screen("renmodpy_records") and renpy.get_screen("renmodpy_linked_record")
            row = renpy.get_screen_variable("linked_record", screen="renmodpy_linked_record")
            assert row["id"] == _rm_check_probe.sharing_identifier
            form = renpy.get_screen_variable("form", screen="renmodpy_records")
            assert form is _rm_check_probe.link_form and dict(form.values) == _rm_check_probe.sharing_draft
            assert _history_list == _rm_check_probe.link_history
            assert not renpy.get_editable_input_value()[1]
            _rm_check_capture("linked-record")
            _rm_check_probe.mode = "records-link-missing"
            _rm_open_record_link("f" * 32)
            return None
        if mode == "records-link-missing":
            assert renpy.get_screen_variable("linked_record", screen="renmodpy_linked_record") is None
            _rm_check_capture("linked-record-missing")
            _rm_check_probe.mode = "records-link-after-load"
            _rm_close_record_link_after_load()
            return None
        if mode == "records-link-after-load":
            assert not renpy.get_screen("renmodpy_linked_record")
            _rm_check_probe.mode = "records-link-back"
            _rm_open_record_link(_rm_check_probe.sharing_identifier)
            return None
        if mode == "records-link-back":
            assert renpy.get_screen("renmodpy_linked_record")
            _rm_check_probe.mode = "records-link-closed"
            _rm_check_pygame.event.post(_rm_check_pygame.event.Event(_rm_check_pygame.KEYDOWN,
                key=_rm_check_pygame.K_AC_BACK, mod=0, unicode="", scancode=0, repeat=False))
            _rm_check_pygame.event.post(_rm_check_pygame.event.Event(_rm_check_pygame.KEYUP,
                key=_rm_check_pygame.K_AC_BACK, mod=0, unicode="", scancode=0, repeat=False))
            return None
        if mode == "records-link-closed":
            assert not renpy.get_screen("renmodpy_linked_record")
            form = renpy.get_screen_variable("form", screen="renmodpy_records")
            assert form is _rm_check_probe.link_form and dict(form.values) == _rm_check_probe.sharing_draft
            assert form.editing_id == _rm_check_probe.sharing_identifier and not form.needs_reload
            assert _history_list == _rm_check_probe.link_history and not renpy.get_editable_input_value()[1]
            _rm_check_probe.mode = "records-edit"
            return None
        if mode == "records-edit":
            form = renpy.get_screen_variable("form", screen="renmodpy_records")
            _rm_check_capture(mode)
            _rm_submit_record(form, "records", _rm_services.records().snapshot()["revision"])
            row = _rm_services.records().list()[0]
            assert row["values"]["extra"] == "Keep outside the visible schema"
            assert row["values"]["body"] == "Edited note\nwith Unicode Blåbær"
            assert form.editing_id is None and not any(form.values.values())
            _rm_check_probe.mode = "records-saved"
            return None
        if mode == "records-saved":
            _rm_check_capture(mode)
            return True
        if mode == "dialogue-home":
            if not renpy.get_screen("say"):
                return None
            _rm_check_capture("dialogue")
            _rm_check_probe.mode = "home-return"
            renpy.run([Function(_rm_return_home), ShowMenu("renmodpy_home")])
            return None
        if mode == "home-return":
            assert renpy.get_screen("renmodpy_home"), "Home did not open from dialogue"
            assert renmodpy_check_counter == 3
            assert renpy.can_load(_rm_services.RESUME_SLOT)
            _rm_check_capture("story-home")
            _rm_check_probe.mode = "history-menu"
            renpy.run(ShowMenu("renmodpy_history"))
            return None
        if mode == "history-menu":
            assert renpy.get_screen("renmodpy_history")
            assert renmodpy_check_counter == 3
            assert any("This dialogue waits" in (entry.what or "") for entry in _history_list)
            _rm_copy_history("{b}This dialogue waits{/b}\nBlåbær")
            assert _rm_services.clipboard_text() == "This dialogue waits\nBlåbær"
            _rm_share_history("{b}This dialogue waits{/b}\nBlåbær")
            assert renmodpy_check_counter == 3 and _rm_services.clipboard_text() == "This dialogue waits\nBlåbær"
            _rm_check_capture("history")
            _rm_check_probe.mode = "settings-menu"
            renpy.run(ShowMenu("renmodpy_settings"))
            return None
        if mode == "settings-menu":
            assert renpy.get_screen("renmodpy_settings")
            _rm_reading_preference("font size", 1.0)
            _rm_reading_preference("text speed", 30)
            assert _preferences.font_size == 1.0 and _preferences.text_cps == 30
            _rm_check_capture("settings")
            _rm_check_probe.mode = "records-menu"
            renpy.run(ShowMenu("renmodpy_records"))
            return None
        if mode == "records-menu":
            assert renpy.get_screen("renmodpy_records") and renmodpy_check_counter == 3
            assert not _rm_services.records().list()
            _rm_check_probe.mode = "home-back"
            renpy.run(ShowMenu("renmodpy_home"))
            return None
        if mode == "home-back":
            assert renpy.get_screen("renmodpy_home") and renmodpy_check_counter == 3
            _rm_check_probe.mode = "finish-dialogue"
            return True
        if mode == "finish-dialogue":
            assert renpy.get_screen("say"), "Return did not resume dialogue"
            assert renmodpy_check_counter == 3
            return True
        if mode == "saved-catalog":
            assert renpy.get_screen("renmodpy_saves")
            _rm_check_capture("saved-catalog")
            _rm_check_list("renmodpy_saves", "saves_list", "entries")
            return True
        if mode == "replay-confirm":
            assert renpy.get_screen("renmodpy_home") and renmodpy_check_counter == 1
            _rm_check_probe.mode = "replay-accept"
            renpy.run(Show("confirm", message="Restart this story?",
                yes_action=Function(_rm_restart_story, "start"), no_action=Hide("confirm")))
            return None
        if mode == "replay-accept":
            assert renpy.get_screen("confirm")
            _rm_check_capture("replay-confirm")
            renpy.run([Hide("confirm"), Function(_rm_restart_story, "start")])
            return None
        if not renpy.get_screen("renmodpy_tactics"):
            return None
        board = renpy.get_screen_variable("board", screen="renmodpy_tactics")
        assert board._raster_surface is not None, "Board was not rendered"
        if mode == "replay-home":
            _rm_check_probe.mode = "replay-confirm"
            renpy.run([Function(_rm_return_home), ShowMenu("renmodpy_home")])
            return None
        if mode == "configure-board":
            assert _renmodpy_board.move_tactics_unit(_renmodpy_board.revision, _rm_check_Cell(1, 0, 0))
            board.change_view(rotation=1, zoom=1.2, opacity=0.55, pan_x=10.0)
            _rm_check_probe.mode = "save-board"
            renpy.restart_interaction()
            return None
        if mode == "save-board":
            _rm_check_capture("tactics")
            _rm_services.save_resume()
            assert _rm_services.resume_slot() == _rm_services.RESUME_SLOT
            assert FileLoad(_rm_services.resume_slot(), slot=True).get_sensitive()
            _rm_services.save_quick()
            assert _rm_services.quick_available()
            slot = _rm_services.create_save("Native checkpoint", "The balcony route")
            entry = next(r for r in _rm_services.save_catalog() if r["slot"] == slot)
            assert entry["name"] == "Native checkpoint" and entry["supported"]
            _rm_check_write("checkpoint.json", {"slot": slot, "board": _renmodpy_board.snapshot()})
            _rm_services.records().create({"title": "Newer {application} [data]", "body": "Kept after load"})
            renpy.run(Preference("font size", 1.25))
            renpy.run(Preference("text speed", 0))
            renpy.save_persistent()
            _renmodpy_board.reset_tactics(_renmodpy_board.revision)
            renpy.store.renmodpy_check_counter = 99
            renpy.quit(status=0, save=False)
        if mode == "reloaded-tactics":
            _rm_check_capture(mode)
            board.skip()
            return "skipped"
        raise AssertionError("Unknown native probe stage: " + mode)

screen renmodpy_check_driver():
    zorder 300
    timer 0.7 action Function(_rm_check_tick) repeat True

default renmodpy_check_counter = 0

label renmodpy_check_start:
    $ main_menu = True
    call screen renmodpy_home
    $ main_menu = False
    $ renmodpy_check_counter = 3
    $ _rm_check_probe.mode = "dialogue-home"
    narrator "This dialogue waits while you visit Home. Resume brings you back here."
    $ assert renmodpy_check_counter == 3
    $ _rm_services.records().create({"title": "Before save", "body": "A lighthouse note", "extra": "Keep outside the visible schema"})
    $ _rm_check_probe.mode = "records"
    call screen renmodpy_records
    $ _rm_check_probe.mode = "saves"
    call screen renmodpy_saves
    $ renmodpy_check_counter = 1
    $ _rm_check_probe.mode = "configure-board"
    call renmodpy_tactics from renmodpy_check_tactics_return
    $ assert _rm_check_probe.phase in ("reload", "quick") and _return == "skipped"
    if _rm_check_probe.phase == "quick":
        $ assert _rm_services.quick_available() and len(_rm_services.records().list()) == 2
        $ _rm_check_savedirs("quick-before-save")
        $ _rm_services.create_save("Replay checkpoint", "After quick load")
        $ _rm_check_savedirs("quick-after-save")
        $ _rm_check_write("quick-passed.json", {"result": "passed"})
        $ renpy.quit(status=0, save=False)
    $ _rm_check_probe.mode = "saved-catalog"
    call screen renmodpy_saves
    python:
        assert _rm_check_probe.phase == "reload"
        _rm_services.finish_story("Native probe finished")
        assert _rm_services.resume_slot() is None
        entries = _rm_services.save_catalog()
        assert len(entries) == 1, "Completion lost named checkpoints"
        entry = entries[0]
        _rm_services.overwrite_save(entry["slot"], entry["fingerprint"], "Overwritten", "Completed")
        try:
            _rm_services.delete_save(entry["slot"], entry["fingerprint"])
        except ValueError:
            pass
        else:
            raise AssertionError("A stale delete removed an overwritten checkpoint")
        current = _rm_services.save_catalog()[0]
        _rm_services.delete_save(current["slot"], current["fingerprint"])
        assert not _rm_services.save_catalog()
        _rm_check_savedirs("after-delete")
        assert len(_rm_services.records().list()) == 2
        _rm_check_write("runtime-passed.json", {"result": "passed", "engine": renpy.version_string,
            "checks": ["home/records/saves rendered", "dialogue/home/resume round trip",
                "history/settings/records menus preserve the dialogue interaction",
                "record edit/reload keeps drafts and invisible fields", "multiline record input",
                "SDL clipboard Unicode/multiline copy/paste and plain history export",
                "sharing unavailable on the host preserves Records drafts and the story session",
                "Android-only Records share controls evaluate and disable input without changing the draft",
                "linked Record overlay renders current saved data and preserves the underlying edited form, inactive input and waiting story",
                "missing Record links, the after-load dismissal and SDL Android Back events preserve drafts and story history",
                "backup preview/confirmed import keeps edited drafts and hidden fields and requires reload",
                "casefold Records sorting and saved order retain stored rows and the edited draft",
                "reading settings survive restart and older story load",
                "populated save browser rendered", "native board rendered",
                "durable resume exact slot", "named checkpoint create/overwrite/delete",
                "real engine restart/load", "board and camera restored", "story variable restored",
                "newer records preserved", "completion clears resume but keeps named checkpoints"]})
        renpy.quit(status=0, save=False)

label renmodpy_check_restarted:
    $ _rm_services.begin_story()
    $ assert renmodpy_check_counter == 0 and not _history_list
    $ assert len(_rm_services.records().list()) == 2 and _rm_services.quick_available()
    $ assert [row["name"] for row in _rm_services.save_catalog()] == ["Replay checkpoint"], repr(_rm_services.save_catalog())
    $ assert _rm_services.resume_slot() is None
    $ assert _preferences.font_size == 1.25 and _preferences.text_cps == 0
    $ _rm_check_write("replay-passed.json", {"result": "passed"})
    $ renpy.quit(status=0, save=False)
