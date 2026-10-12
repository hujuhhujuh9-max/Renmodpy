# RenModPy built-in screens and native entry points.
# Installed into renpy/common by build_sdk.py and packaged by ordinary RAPT.

init -800 python:
    from renpy import renmodpy
    from renpy.renmodpy import services as _rm_services
    from renpy.renmodpy import transfers as _rm_transfers
    from renpy.renmodpy.board import TacticsDisplayable as _rm_TacticsDisplayable
    import datetime as _rm_datetime

    def _rm_literal(value):
        return str(value).replace("{", "{{").replace("[", "[[")

    def _rm_record_snapshot(collection="records"):
        try:
            return _rm_services.records(collection).snapshot(), ""
        except (ValueError, renmodpy.RecordsError) as error:
            return {"revision": 0, "records": []}, str(error)

    def _rm_submit_record(form, collection, revision):
        if form.submit(_rm_services.records(collection), revision) and renpy.android:
            try:
                _rm_services.haptic("confirm")
            except RuntimeError:
                pass

    def _rm_edit_record(form, snapshot, identifier):
        try:
            form.edit(snapshot, identifier)
        except renmodpy.RecordsError as error:
            form.message = str(error)
            form.needs_reload = True

    def _rm_reload_records(form, collection):
        try:
            form.reload(_rm_services.records(collection).snapshot())
        except (ValueError, renmodpy.RecordsError) as error:
            form.message = str(error)
            form.needs_reload = True

    def _rm_copy_record(values, fields, form):
        text = _rm_record_text(values, fields)
        try:
            _rm_services.copy_text(text)
            form.message = "Record copied."
        except (ValueError, _rm_services.ClipboardError) as error:
            form.message = str(error)

    def _rm_record_text(values, fields):
        return "\n\n".join(values.get(field.name, "") for field in fields if values.get(field.name))

    def _rm_share_record(values, fields, form):
        try:
            _rm_services.share_text(_rm_record_text(values, fields))
            form.message = "Choose an app to share this record."
        except (ValueError, _rm_services.ShareError) as error:
            form.message = str(error) + " Your draft is kept."

    def _rm_paste_record(form, name):
        try:
            form.paste(name, _rm_services.clipboard_text())
        except _rm_services.ClipboardError as error:
            form.message = str(error) + " Your draft is kept."

    def _rm_copy_history(text):
        try:
            _rm_services.copy_text(renpy.filter_text_tags(text or "", allow=set()))
            renpy.notify("Dialogue copied.")
        except (ValueError, _rm_services.ClipboardError) as error:
            renpy.notify(str(error))

    def _rm_share_history(text):
        try:
            _rm_services.share_text(renpy.filter_text_tags(text or "", allow=set()))
        except (ValueError, _rm_services.ShareError) as error:
            renpy.notify(str(error))

    def _rm_transfer_current(transfer):
        screen = renpy.get_screen("renmodpy_records")
        return screen is not None and screen.scope.get("transfer") is transfer

    def _rm_preview_records(form, collection, transfer):
        snapshot = _rm_services.records(collection).snapshot()
        current = {row["id"]: row["values"] for row in snapshot["records"]}
        for index, row in enumerate(transfer["rows"], 1):
            values = dict(current.get(row["id"], {}), **row["values"])
            for field in form.fields:
                value = values.get(field.name, "")
                if (field.required and not value.strip()) or len(value) > field.max_length:
                    raise ValueError("Backup record %d has an invalid %s." % (index, field.label))
        transfer["preview"] = _rm_transfers.preview_records(transfer["rows"], snapshot)

    def _rm_import_records(form, collection, transfer):
        def finished(text, error):
            if not _rm_transfer_current(transfer):
                return
            transfer["busy"] = False
            if error or text is None:
                form.message = (error or "Import cancelled.") + " Your draft is kept."
            else:
                try:
                    transfer["rows"] = _rm_transfers.load_records(text)
                    _rm_preview_records(form, collection, transfer)
                    form.message = "Review the backup before importing. Your draft is kept."
                except (ValueError, renmodpy.RecordsError) as failed:
                    transfer["rows"], transfer["preview"] = None, None
                    form.message = str(failed) + " Your records and draft are kept."
            renpy.restart_interaction()
        try:
            transfer["busy"] = True
            transfer["rows"], transfer["preview"] = None, None
            _rm_services.pick_text(finished, mime="application/json")
        except (ValueError, _rm_services.FileError) as error:
            transfer["busy"] = False
            form.message = str(error) + " Your draft is kept."

    def _rm_export_records(form, collection, transfer):
        def finished(written, error):
            if not _rm_transfer_current(transfer):
                return
            transfer["busy"] = False
            form.message = (error or ("Backup exported." if written else "Export cancelled.")) + " Your draft is kept."
            renpy.restart_interaction()
        try:
            text = _rm_transfers.dump_records(_rm_services.records(collection).snapshot())
            transfer["busy"] = True
            _rm_services.export_text(collection + ".json", text, finished, mime="application/json")
        except (ValueError, renmodpy.RecordsError, _rm_services.FileError) as error:
            transfer["busy"] = False
            form.message = str(error) + " Your draft is kept."

    def _rm_share_backup(form, collection):
        try:
            text = _rm_transfers.dump_records(_rm_services.records(collection).snapshot())
            _rm_services.share_file(collection + ".json", text.encode("utf-8"), mime="application/json")
            form.message = "Choose an app to share the backup. Your draft is kept."
        except (ValueError, renmodpy.RecordsError, _rm_services.ShareError) as error:
            form.message = str(error) + " Your draft is kept."

    def _rm_apply_import(form, collection, transfer):
        try:
            _rm_services.records(collection).merge(transfer["rows"], expected_revision=transfer["preview"]["revision"])
            transfer["rows"], transfer["preview"] = None, None
            if form.editing_id is not None:
                form.needs_reload = True
            form.message = "Backup imported. Your draft is kept." + (" Reload records before saving." if form.needs_reload else "")
        except (ValueError, renmodpy.RecordsError) as error:
            form.message = str(error) + " Preview the backup again. Your draft is kept."

    def _rm_refresh_preview(form, collection, transfer):
        try:
            _rm_preview_records(form, collection, transfer)
            form.message = "Backup preview refreshed. Your draft is kept."
        except (ValueError, renmodpy.RecordsError) as error:
            form.message = str(error) + " Your records and draft are kept."

    def _rm_transfer_recovery(form, transfer):
        if transfer["busy"] and not _rm_services.file_request_pending():
            transfer["busy"] = False
            form.message = "The file request ended. Choose a file again. Your draft is kept."

    def _rm_delete_record(identifier, revision, form, collection):
        try:
            records = _rm_services.records(collection)
            records.delete(identifier, expected_revision=revision)
            form.message = "Record deleted."
            if form.editing_id == identifier:
                form.reload(records.snapshot())
        except (ValueError, renmodpy.RecordsError) as error:
            form.message = str(error) + " Reload records; your draft is kept."
            form.needs_reload = True

    def _rm_save_catalog():
        try:
            return _rm_services.save_catalog(), ""
        except (OSError, ValueError) as error:
            return [], str(error)

    def _rm_save_action(action, slot=None, fingerprint=None, name=""):
        try:
            scene = getattr(renpy.store, "renmodpy_scene", "Story")
            if action == "create":
                _rm_services.create_save(name, scene)
            elif action == "overwrite":
                _rm_services.overwrite_save(slot, fingerprint, name, scene)
            elif action == "delete":
                _rm_services.delete_save(slot, fingerprint)
            elif action == "load":
                _rm_services.load_save(slot, fingerprint)
            message = {"create": "Save created.", "overwrite": "Save overwritten.",
                       "delete": "Save deleted.", "load": "Story loaded."}[action]
        except (OSError, ValueError) as error:
            message = str(error)
        renpy.set_screen_variable("message", message, screen="renmodpy_saves")

    def _rm_return_home():
        try:
            _rm_services.save_resume()
        except (OSError, ValueError) as error:
            renpy.notify("Resume bookmark could not be saved: " + str(error))

    def _rm_quick_action(action):
        try:
            if action == "save":
                _rm_services.save_quick()
            else:
                _rm_services.load_quick()
            message = "Quick save created."
        except (OSError, ValueError) as error:
            message = str(error)
        renpy.set_screen_variable("message", message, screen="renmodpy_home")

    def _rm_reading_preference(name, value):
        renpy.run(Preference(name, value))
        try:
            renpy.save_persistent()
            message = "Reading settings saved."
        except OSError:
            message = "Reading settings could not be saved. Try again."
        renpy.set_screen_variable("message", message, screen="renmodpy_settings")

    def _rm_restart_story(story_label):
        # Start jumps to a label in the existing store. A replay needs the
        # engine's restart path to reset defaults, call stacks and history.
        renpy.full_restart(label="renmodpy_restart", target=story_label, save=False)

init 800 python:
    _rm_services.bind(renpy)
    if _rm_services.poll_services not in config.periodic_callbacks:
        config.periodic_callbacks.append(_rm_services.poll_services)

default _renmodpy_board = None
default renmodpy_scene = "Story"
default _renmodpy_restart_target = "start"
default persistent.renmodpy_last_result = None

init -700 python:
    if config.history_length is None:
        config.history_length = 200

init -700:
    style renmodpy_text is default:
        size 28
        color "#e9f1f4"
    style renmodpy_heading is renmodpy_text:
        size 44
        bold True
    style renmodpy_caption is renmodpy_text:
        size 22
        color "#acbeca"
    style renmodpy_button is button:
        background Solid("#24434b")
        hover_background Solid("#35626a")
        insensitive_background Solid("#202c35")
        padding (22, 16)
        yminimum 72
    style renmodpy_button_text is renmodpy_text:
        hover_color "#ffffff"
        insensitive_color "#647583"
    style renmodpy_clipboard_button is renmodpy_button:
        padding (12, 8)
        yminimum 44
    style renmodpy_clipboard_button_text is renmodpy_button_text:
        size 22
    style renmodpy_input is input:
        size 28
        color "#ffffff"
    style renmodpy_frame is frame:
        background Solid("#182b36")
        padding (20, 18)
        xalign 0.0
        yalign 0.0
    style renmodpy_viewport is viewport:
        xfill True
        yfill True
    style renmodpy_vscrollbar is vscrollbar:
        xsize 18
        base_bar Solid("#182b36")
        thumb Solid("#35626a")
        unscrollable "hide"

define renmodpy_home_links = ()

screen renmodpy_home(story_label="start"):
    tag menu
    style_prefix "renmodpy"
    default message = ""
    add Solid("#101d27")
    viewport:
        id "home_content"
        xpos 36
        ypos 44
        xsize 648
        ysize 1192
        draggable True
        mousewheel True
        scrollbars "vertical"
        vbox:
            xsize 620
            spacing 18
            text "RenModPy" style "renmodpy_heading"
            text "Stories and app features in one engine." style "renmodpy_caption"
            null height 12
            if main_menu:
                textbutton "Start story" action Start(story_label) xfill True
                $ resume_slot = _rm_services.resume_slot()
                textbutton "Resume story":
                    xfill True
                    sensitive resume_slot is not None
                    action FileLoad(resume_slot, slot=True, confirm=False)
            else:
                textbutton "Resume story" action Return() xfill True
            hbox:
                spacing 12
                textbutton "Quick save":
                    sensitive not main_menu
                    action Function(_rm_quick_action, "save")
                textbutton "Quick load":
                    sensitive _rm_services.quick_available()
                    action Show("confirm", message="Load your quick save?",
                        yes_action=Function(_rm_quick_action, "load"), no_action=Hide("confirm"))
            if message:
                text _rm_literal(message) style "renmodpy_caption"
            textbutton "Records" action ShowMenu("renmodpy_records") xfill True
            textbutton "Saved games" action ShowMenu("renmodpy_saves") xfill True
            textbutton "Story history" action ShowMenu("renmodpy_history") xfill True
            textbutton "Reading settings" action ShowMenu("renmodpy_settings") xfill True
            for caption, menu_screen in renmodpy_home_links:
                textbutton caption action ShowMenu(menu_screen) xfill True
            if not main_menu:
                textbutton "Replay story":
                    xfill True
                    action Show("confirm", message="Restart this story? Quick and named saves are kept.",
                        yes_action=Function(_rm_restart_story, story_label), no_action=Hide("confirm"))
            if persistent.renmodpy_last_result:
                frame:
                    xfill True
                    text _rm_literal(persistent.renmodpy_last_result)
            textbutton "Close app" action Quit(confirm=True) xfill True
    key "game_menu" action (Quit(confirm=True) if main_menu else Return())

screen renmodpy_history():
    tag menu
    style_prefix "renmodpy"
    add Solid("#101d27")
    viewport:
        id "history_content"
        xpos 36
        ypos 36
        xsize 648
        ysize 1208
        draggable True
        mousewheel True
        scrollbars "vertical"
        vbox:
            xsize 620
            spacing 18
            hbox:
                spacing 18
                text "Story history" style "renmodpy_heading" xsize 440 layout "greedy"
                textbutton "Home" action ShowMenu("renmodpy_home")
            for entry in _history_list:
                frame:
                    xfill True
                    vbox:
                        spacing 10
                        if entry.who:
                            text _rm_literal(entry.who) bold True
                        text renpy.filter_text_tags(entry.what or "", allow={"b", "i", "u", "s", "color"}):
                            substitute False
                        hbox:
                            spacing 12
                            style_prefix "renmodpy_clipboard"
                            textbutton "Copy line" action Function(_rm_copy_history, entry.what)
                            if renpy.android:
                                textbutton "Share line" action Function(_rm_share_history, entry.what)
            if not _history_list:
                text "Dialogue will appear here as you read." style "renmodpy_caption"
    key "game_menu" action ShowMenu("renmodpy_home")

screen renmodpy_settings():
    tag menu
    style_prefix "renmodpy"
    default message = ""
    add Solid("#101d27")
    viewport:
        id "settings_content"
        xpos 36
        ypos 36
        xsize 648
        ysize 1208
        draggable True
        mousewheel True
        scrollbars "vertical"
        vbox:
            xsize 620
            spacing 24
            hbox:
                spacing 18
                text "Reading settings" style "renmodpy_heading" xsize 440 layout "greedy"
                textbutton "Home" action ShowMenu("renmodpy_home")
            text ("Text size: Larger" if _preferences.font_size > 1.0 else "Text size: Standard"):
                style "renmodpy_caption"
            hbox:
                spacing 12
                textbutton "Standard" action Function(_rm_reading_preference, "font size", 1.0)
                textbutton "Larger" action Function(_rm_reading_preference, "font size", 1.25)
            text "A clear sky, a quiet morning. Your place in the story is kept."
            text ("Dialogue: Instant" if _preferences.text_cps == 0 else "Dialogue: Animated"):
                style "renmodpy_caption"
            hbox:
                spacing 12
                textbutton "Animated" action Function(_rm_reading_preference, "text speed", 30)
                textbutton "Instant" action Function(_rm_reading_preference, "text speed", 0)
            text "With animated dialogue, tap once to reveal the line, then again to continue.":
                style "renmodpy_caption"
            text "These settings stay current when you load an older story save.":
                style "renmodpy_caption"
            text _rm_literal(message) style "renmodpy_caption"
    key "game_menu" action ShowMenu("renmodpy_home")

screen renmodpy_records(collection="records", title="Records", fields=renmodpy.DEFAULT_FIELDS):
    tag menu
    style_prefix "renmodpy"
    default form = renmodpy.RecordDraft(fields)
    default transfer = {"busy": False, "rows": None, "preview": None}
    default sort_mode = "saved"
    default input_values = {field.name: DictInputValue(form.values, field.name, default=(index == 0)) for index, field in enumerate(form.fields)}
    $ snapshot, read_error = _rm_record_snapshot(collection)
    $ displayed_records = (sorted(snapshot["records"], key=lambda record, field=form.fields[0].name: record["values"].get(field, "").casefold()) if sort_mode == "title" else snapshot["records"])
    $ _rm_transfer_recovery(form, transfer)
    add Solid("#101d27")
    viewport:
        id "records_list"
        xpos 36
        ypos 36
        xsize 648
        ysize 1208
        draggable True
        mousewheel True
        scrollbars "vertical"
        vbox:
            xsize 620
            spacing 14
            hbox:
                spacing 18
                text _rm_literal(title) style "renmodpy_heading" xsize 440 layout "greedy"
                textbutton "Home" action ShowMenu("renmodpy_home")
            text "Application data stays current when a story is loaded." style "renmodpy_caption"
            if renpy.android:
                hbox:
                    spacing 12
                    style_prefix "renmodpy_clipboard"
                    textbutton "Import backup":
                        sensitive not transfer["busy"]
                        action [value.Disable() for value in input_values.values()] + [Function(_rm_import_records, form, collection, transfer)]
                    textbutton "Export backup":
                        sensitive not read_error and not transfer["busy"]
                        action [value.Disable() for value in input_values.values()] + [Function(_rm_export_records, form, collection, transfer)]
                textbutton "Share backup":
                    style_prefix "renmodpy_clipboard"
                    sensitive not read_error and not transfer["busy"]
                    action [value.Disable() for value in input_values.values()] + [Function(_rm_share_backup, form, collection)]
                text "Backups include all saved fields. Drafts stay on this screen." style "renmodpy_caption"
                if transfer["busy"]:
                    text "Waiting for the file request…" style "renmodpy_caption"
            if transfer["preview"] is not None:
                frame:
                    xfill True
                    vbox:
                        spacing 12
                        text "Backup preview" style "renmodpy_text" bold True
                        text ("%d new, %d updated, %d unchanged." % (transfer["preview"]["new"], transfer["preview"]["updated"], transfer["preview"]["unchanged"])) style "renmodpy_caption"
                        text "Other records and omitted fields are kept." style "renmodpy_caption"
                        hbox:
                            spacing 12
                            style_prefix "renmodpy_clipboard"
                            textbutton "Import these records":
                                sensitive not transfer["busy"]
                                action Function(_rm_apply_import, form, collection, transfer)
                            textbutton "Preview again" action Function(_rm_refresh_preview, form, collection, transfer)
                        textbutton "Cancel import":
                            style_prefix "renmodpy_clipboard"
                            action [SetDict(transfer, "rows", None), SetDict(transfer, "preview", None)]
            for field in form.fields:
                hbox:
                    spacing 12
                    text _rm_literal(field.label) style "renmodpy_caption" xsize 440
                    textbutton "Paste":
                        style_prefix "renmodpy_clipboard"
                        action [input_values[field.name].Disable(), Function(_rm_paste_record, form, field.name)]
                button:
                    xfill True
                    action input_values[field.name].Toggle()
                    yminimum (156 if field.multiline else 72)
                    input:
                        id ("record_" + field.name)
                        value input_values[field.name]
                        length field.max_length
                        multiline field.multiline
                        xsize 576
            hbox:
                spacing 12
                textbutton ("Save changes" if form.editing_id else "Add record"):
                    sensitive not read_error and not form.needs_reload
                    action Function(_rm_submit_record, form, collection, snapshot["revision"])
                textbutton "Cancel edit":
                    sensitive form.editing_id is not None or any(form.values.values())
                    action Function(form.cancel)
            text _rm_literal(read_error or form.message) style "renmodpy_caption"
            textbutton "Reload records" action Function(_rm_reload_records, form, collection)
            hbox:
                spacing 12
                style_prefix "renmodpy_clipboard"
                textbutton "Saved order":
                    selected sort_mode == "saved"
                    action SetScreenVariable("sort_mode", "saved")
                textbutton (form.fields[0].label + " A–Z"):
                    selected sort_mode == "title"
                    action SetScreenVariable("sort_mode", "title")
            null height 10
            vbox:
                xsize 620
                spacing 16
                for record in displayed_records:
                    frame:
                        xsize 620
                        vbox:
                            spacing 10
                            for field in form.fields:
                                text _rm_literal(record["values"].get(field.name, "")):
                                    size (28 if field == form.fields[0] else 24)
                                    bold field == form.fields[0]
                            hbox:
                                spacing 12
                                textbutton "Edit":
                                    sensitive not read_error and not form.needs_reload
                                    action Function(_rm_edit_record, form, snapshot, record["id"])
                                textbutton "Delete":
                                    sensitive not read_error and not form.needs_reload
                                    action Show("confirm",
                                        message="Delete this record?",
                                        yes_action=Function(_rm_delete_record, record["id"], snapshot["revision"], form, collection),
                                        no_action=Hide("confirm"))
                            hbox:
                                spacing 12
                                style_prefix "renmodpy_clipboard"
                                textbutton "Copy record" action Function(_rm_copy_record, record["values"], form.fields, form)
                                if renpy.android:
                                    textbutton "Share record":
                                        id ("record_share_" + record["id"])
                                        action [value.Disable() for value in input_values.values()] + [Function(_rm_share_record, record["values"], form.fields, form)]
                if not snapshot["records"] and not read_error:
                    text "Your saved records will appear here." style "renmodpy_caption"
    key "game_menu" action ShowMenu("renmodpy_home")

screen renmodpy_saves():
    tag menu
    style_prefix "renmodpy"
    default save_name = ""
    default save_input = ScreenVariableInputValue("save_name")
    default message = ""
    $ entries, read_error = _rm_save_catalog()
    add Solid("#101d27")
    vbox:
        xpos 36
        ypos 36
        xsize 648
        spacing 16
        hbox:
            spacing 18
            text "Saved games" style "renmodpy_heading" xsize 440 layout "greedy"
            textbutton "Home" action ShowMenu("renmodpy_home")
        if not main_menu:
            text "Name this checkpoint" style "renmodpy_caption"
            button:
                xfill True
                action save_input.Toggle()
                input value save_input length 80 xsize 600
            textbutton "Create save":
                xfill True
                action Function(_rm_save_action, "create", name=save_name)
        text _rm_literal(read_error or message) style "renmodpy_caption"
        viewport:
            id "saves_list"
            ysize (860 if main_menu else 690)
            xfill True
            draggable True
            mousewheel True
            scrollbars "vertical"
            vbox:
                xsize 620
                spacing 16
                for entry in entries:
                    frame:
                        xsize 620
                        vbox:
                            spacing 12
                            text _rm_literal(entry["name"]) bold True
                            text _rm_literal(entry["scene"]) style "renmodpy_caption"
                            text _rm_datetime.datetime.fromtimestamp(entry["time"]).strftime("%Y-%m-%d %H:%M"):
                                style "renmodpy_caption"
                            hbox:
                                spacing 8
                                textbutton "Load":
                                    sensitive entry["supported"]
                                    action Show("confirm", message="Load this checkpoint?",
                                        yes_action=Function(_rm_save_action, "load", entry["slot"], entry["fingerprint"]),
                                        no_action=Hide("confirm"))
                                if not main_menu:
                                    textbutton "Overwrite":
                                        action Show("confirm", message="Overwrite this checkpoint?",
                                            yes_action=Function(_rm_save_action, "overwrite", entry["slot"], entry["fingerprint"], entry["name"]),
                                            no_action=Hide("confirm"))
                                textbutton "Delete":
                                    action Show("confirm", message="Delete this checkpoint?",
                                        yes_action=Function(_rm_save_action, "delete", entry["slot"], entry["fingerprint"]),
                                        no_action=Hide("confirm"))
                if not entries and not read_error:
                    text "Create checkpoints from an active story." style "renmodpy_caption"
    key "game_menu" action ShowMenu("renmodpy_home")

screen renmodpy_tactics(session):
    style_prefix "renmodpy"
    default board = _rm_TacticsDisplayable(session)
    add Solid("#101d27")
    vbox:
        xpos 24
        ypos 30
        xsize 672
        spacing 12
        text "The balcony route" style "renmodpy_heading"
        text "Guide the teal Scout to the gold L2 marker." style "renmodpy_caption"
        add board xsize 672 ysize 610
        text board.view_label() style "renmodpy_caption"
        hbox:
            spacing 8
            textbutton "Iso" action Function(board.set_mode, "isometric")
            textbutton "Top" action Function(board.set_mode, "top_down")
            textbutton "Side" action Function(board.set_mode, "side")
        hbox:
            spacing 8
            textbutton "Rotate" action Function(board.rotate, 1)
            textbutton "−" action Function(board.zoom_by, -0.1)
            textbutton "+" action Function(board.zoom_by, 0.1)
            textbutton "Center" action Function(board.center)
        hbox:
            spacing 8
            for level in (0, 1, 2):
                textbutton ("L" + str(level)) action Function(board.set_level, level)
            textbutton "All" action Function(board.set_level, None)
        text board.input_hint() style "renmodpy_caption"
        hbox:
            spacing 10
            textbutton "Reset" action Function(board.reset)
            textbutton "Skip" action [Function(board.skip), Return("skipped")]
            textbutton "Home" action [Function(_rm_return_home), ShowMenu("renmodpy_home")]
    key "game_menu" action [Function(_rm_return_home), ShowMenu("renmodpy_home")]

label renmodpy_restart:
    $ _renmodpy_restart_target = _restart[2]
    $ renpy.game.log.block_load(purge=True)
    $ _rm_services.begin_story()
    jump expression _renmodpy_restart_target

label renmodpy_tactics:
    $ _renmodpy_board = renmodpy.BoardSession()
    $ renpy.retain_after_load()
label .wait:
    call screen renmodpy_tactics(_renmodpy_board)
    return _return
