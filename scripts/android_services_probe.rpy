# Interactive validation fixture, copied only into the disposable test APK.
# The host taps these ordinary project buttons. No service runs automatically.

init 900 python:
    import threading as _rm_validation_threading
    import types as _rm_validation_types
    import sys as _rm_validation_sys

    _rm_validation = _rm_validation_types.ModuleType("renmodpy_service_fixture")
    _rm_validation_sys.modules[_rm_validation.__name__] = _rm_validation
    _rm_validation.state = {"operation": "", "result": "idle", "owner_thread": False}
    _rm_validation.key = "validation.private-note"
    _rm_validation.first = "First public fixture café Ω"
    _rm_validation.newer = "Newer public fixture café Ω"

    def _rm_validation_request(operation):
        _rm_validation.state = {"operation": operation, "result": "pending", "owner_thread": False}
        def finished(value, error):
            assert _rm_services.owner() is renpy
            matched = ((value == _rm_validation.first) if operation == "read-first" else
                       (value == _rm_validation.newer) if operation == "read-newer" else
                       (value is None) if operation == "read-missing" else
                       (type(value) is bool) if operation == "haptic" else value is True)
            _rm_validation.state = {"operation": operation, "result": "passed" if matched and error is None else "failed",
                "owner_thread": _rm_validation_threading.get_ident() == _rm_services._thread,
                "error": error, "value_matches": matched}
            renpy.restart_interaction()
        try:
            if operation in ("store-first", "store-newer"):
                _rm_services.secure_set(_rm_validation.key,
                    _rm_validation.first if operation == "store-first" else _rm_validation.newer, finished)
            elif operation.startswith("read-"):
                _rm_services.secure_get(_rm_validation.key, finished)
            elif operation == "delete":
                _rm_services.secure_delete(_rm_validation.key, finished)
            else:
                _rm_services.haptic("selection", finished)
        except (ValueError, RuntimeError) as error:
            _rm_validation.state = {"operation": operation, "result": "failed", "error": str(error)}

    config.overlay_screens.append("renmodpy_validation_entry")

screen renmodpy_validation_entry():
    zorder 50
    if renpy.get_screen("renmodpy_home") or renpy.get_screen("main_menu"):
        textbutton "Validation tools":
            style_prefix "renmodpy_clipboard"
            xpos 36
            ypos 1190
            action ShowMenu("renmodpy_validation_tools")

screen renmodpy_validation_tools():
    tag menu
    style_prefix "renmodpy"
    add Solid("#101d27")
    vbox:
        xpos 36
        ypos 44
        xsize 648
        spacing 14
        text "Native service fixture" style "renmodpy_heading"
        textbutton "Store first fixture" action Function(_rm_validation_request, "store-first")
        textbutton "Store newer fixture" action Function(_rm_validation_request, "store-newer")
        textbutton "Read first fixture" action Function(_rm_validation_request, "read-first")
        textbutton "Read newer fixture" action Function(_rm_validation_request, "read-newer")
        textbutton "Delete private fixture" action Function(_rm_validation_request, "delete")
        textbutton "Read missing fixture" action Function(_rm_validation_request, "read-missing")
        textbutton "Touch feedback fixture" action Function(_rm_validation_request, "haptic")
        text _rm_validation.state["result"] style "renmodpy_caption"
        textbutton "Home" action ShowMenu("renmodpy_home")
    key "game_menu" action ShowMenu("renmodpy_home")
