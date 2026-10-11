# RenModPy built-in screens and native entry points.
# Installed into renpy/common by build_sdk.py and packaged by ordinary RAPT.

init -800 python:
    from renpy import renmodpy
    from renpy.renmodpy import services as _rm_services
    from renpy.renmodpy.board import TacticsDisplayable as _rm_TacticsDisplayable
    import datetime as _rm_datetime

    def _rm_literal(value):
        return str(value).replace("{", "{{").replace("[", "[[")

    def _rm_record_snapshot():
        try:
            return _rm_services.records().snapshot(), ""
        except renmodpy.RecordsError as error:
            return {"revision": 0, "records": []}, str(error)

    def _rm_add_record(title, body, revision):
        try:
            if not title.strip():
                raise ValueError("Give the record a title.")
            _rm_services.records().create({"title": title.strip(), "body": body},
                                         expected_revision=revision)
            renpy.set_screen_variable("draft_title", "", screen="renmodpy_records")
            renpy.set_screen_variable("draft_body", "", screen="renmodpy_records")
            message = "Record saved."
        except (ValueError, renmodpy.RecordsError) as error:
            message = str(error)
        renpy.set_screen_variable("message", message, screen="renmodpy_records")

    def _rm_delete_record(identifier, revision):
        try:
            _rm_services.records().delete(identifier, expected_revision=revision)
            message = "Record deleted."
        except (ValueError, renmodpy.RecordsError) as error:
            message = str(error)
        renpy.set_screen_variable("message", message, screen="renmodpy_records")

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

init 800 python:
    _rm_services.bind(renpy)

default _renmodpy_board = None
default renmodpy_scene = "Story"
default persistent.renmodpy_last_result = None

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

screen renmodpy_home(story_label="start"):
    tag menu
    style_prefix "renmodpy"
    add Solid("#101d27")
    vbox:
        xpos 36
        ypos 60
        xsize 648
        spacing 22
        text "RenModPy" style "renmodpy_heading"
        text "Stories and app features in one engine." style "renmodpy_caption"
        null height 18
        if main_menu:
            textbutton "Start story" action Start(story_label) xfill True
            $ resume_slot = _rm_services.resume_slot()
            textbutton "Resume story":
                xfill True
                sensitive resume_slot is not None
                action FileLoad(resume_slot, slot=True, confirm=False)
        else:
            textbutton "Resume story" action Return() xfill True
        textbutton "Records" action ShowMenu("renmodpy_records") xfill True
        textbutton "Saved games" action ShowMenu("renmodpy_saves") xfill True
        if persistent.renmodpy_last_result:
            frame:
                xfill True
                text _rm_literal(persistent.renmodpy_last_result)
        textbutton "Close app" action Quit(confirm=True) xfill True
    key "game_menu" action (Quit(confirm=True) if main_menu else Return())

screen renmodpy_records():
    tag menu
    style_prefix "renmodpy"
    default draft_title = ""
    default draft_body = ""
    default message = ""
    default title_value = ScreenVariableInputValue("draft_title", default=True)
    default body_value = ScreenVariableInputValue("draft_body", default=False)
    $ snapshot, read_error = _rm_record_snapshot()
    add Solid("#101d27")
    vbox:
        xpos 36
        ypos 36
        xsize 648
        spacing 14
        hbox:
            spacing 18
            text "Records" style "renmodpy_heading"
            textbutton "Home" action ShowMenu("renmodpy_home")
        text "Application data stays current when a story is loaded." style "renmodpy_caption"
        text "Title" style "renmodpy_caption"
        button:
            xfill True
            action title_value.Toggle()
            input value title_value length 80 xsize 600
        text "Note" style "renmodpy_caption"
        button:
            xfill True
            action body_value.Toggle()
            input value body_value length 1000 xsize 600
        textbutton "Add record":
            xfill True
            sensitive not read_error
            action Function(_rm_add_record, draft_title, draft_body, snapshot["revision"])
        text _rm_literal(read_error or message) style "renmodpy_caption"
        viewport:
            id "records_list"
            ysize 600
            xfill True
            draggable True
            mousewheel True
            scrollbars "vertical"
            vbox:
                xsize 620
                spacing 16
                for record in snapshot["records"]:
                    frame:
                        xsize 620
                        vbox:
                            spacing 10
                            text _rm_literal(record["values"].get("title", "Record")):
                                bold True
                            text _rm_literal(record["values"].get("body", "")):
                                size 24
                            textbutton "Delete":
                                action Show("confirm",
                                    message="Delete this record?",
                                    yes_action=Function(_rm_delete_record, record["id"], snapshot["revision"]),
                                    no_action=Hide("confirm"))
                if not snapshot["records"] and not read_error:
                    text "Your saved records will appear here." style "renmodpy_caption"
    key "game_menu" action ShowMenu("renmodpy_home")

screen renmodpy_saves():
    tag menu
    style_prefix "renmodpy"
    default save_name = ""
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
            text "Saved games" style "renmodpy_heading"
            textbutton "Home" action ShowMenu("renmodpy_home")
        if not main_menu:
            text "Name this checkpoint" style "renmodpy_caption"
            frame:
                xfill True
                input value ScreenVariableInputValue("save_name") length 80 xsize 600
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

label renmodpy_tactics:
    $ _renmodpy_board = renmodpy.BoardSession()
    $ renpy.retain_after_load()
label .wait:
    call screen renmodpy_tactics(_renmodpy_board)
    return _return
