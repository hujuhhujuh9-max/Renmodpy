# Read-only observer copied only into the disposable emulator-test project.
# The host drives real Android input. The probe only reports state and observes
# the native chooser dispatch requested by an actual tap.

init 900 python:
    import json as _rm_android_json
    import os as _rm_android_os
    import sys as _rm_android_sys
    import types as _rm_android_types
    import uuid as _rm_android_uuid
    import traceback as _rm_android_traceback
    from pathlib import Path as _rm_android_Path

    _rm_android_probe = _rm_android_types.ModuleType("renmodpy_android_probe")
    _rm_android_sys.modules[_rm_android_probe.__name__] = _rm_android_probe
    _rm_android_probe.boot = _rm_android_uuid.uuid4().hex
    _rm_android_probe.sequence = 0
    _rm_android_probe.share_sequence = 0
    _rm_android_probe.worker_events = []
    _rm_android_probe.haptic_events = []
    if renpy.android:
        from jnius import autoclass as _rm_android_autoclass
        _rm_android_activity = _rm_android_autoclass("org.renpy.android.PythonSDLActivity").mActivity
        _rm_android_probe.directory = _rm_android_Path(str(_rm_android_activity.getFilesDir().getAbsolutePath())) / "renmodpy-probe"
        from renpy.renmodpy import android_sharing as _rm_android_sharing
        from renpy.renmodpy import android_jni as _rm_android_jni
        from renpy.renmodpy import android_workers as _rm_android_workers
        from renpy.renmodpy import android_device as _rm_android_device
        _rm_android_probe.worker_run = _rm_android_workers.run
        _rm_android_probe.haptic_perform = _rm_android_device._perform_haptic
        def _rm_android_worker_run(handler, callback, error_message):
            def observed():
                thread = _rm_android_autoclass("java.lang.Thread").currentThread()
                _rm_android_probe.worker_events.append({
                    "app_loader": bool(thread.getContextClassLoader().equals(_rm_android_activity.getClassLoader())),
                    "ui_thread": bool(_rm_android_autoclass("android.os.Looper").getMainLooper().equals(
                        _rm_android_autoclass("android.os.Looper").myLooper()))})
                return handler()
            return _rm_android_probe.worker_run(observed, callback, error_message)
        _rm_android_workers.run = _rm_android_worker_run
        # The importing modules bind run_worker during import; observe both
        # aliases without changing their request/callback behavior.
        _rm_android_device.run_worker = _rm_android_worker_run
        def _rm_android_haptic(activity, code):
            accepted = _rm_android_probe.haptic_perform(activity, code)
            _rm_android_probe.haptic_events.append({"code": code, "accepted": accepted,
                "ui_thread": bool(_rm_android_autoclass("android.os.Looper").getMainLooper().equals(
                    _rm_android_autoclass("android.os.Looper").myLooper()))})
            return accepted
        _rm_android_device._perform_haptic = _rm_android_haptic
        from jnius import cast as _rm_android_cast
        _rm_android_probe.launch = _rm_android_sharing._launch
        _rm_android_probe.request_share = _rm_android_sharing.share_text

        def _rm_android_share_error(error):
            report = {"boot": _rm_android_probe.boot, "error": str(error),
                "type": type(error).__name__, "traceback": "".join(
                    _rm_android_traceback.format_exception(type(error), error, error.__traceback__))}
            temporary = _rm_android_probe.directory / "share-error.tmp"
            temporary.write_text(_rm_android_json.dumps(report, ensure_ascii=False))
            _rm_android_os.replace(temporary, _rm_android_probe.directory / "share-error.json")

        def _rm_android_share_request(text, subject, on_error):
            def failed(error):
                _rm_android_share_error(error)
                on_error(error)
            try:
                return _rm_android_probe.request_share(text, subject, on_error=failed)
            except Exception as error:
                _rm_android_share_error(error)
                raise

        _rm_android_sharing.share_text = _rm_android_share_request

        def _rm_android_share_launch(activity, chooser):
            Intent = _rm_android_autoclass("android.content.Intent")
            Looper = _rm_android_autoclass("android.os.Looper")
            intent = _rm_android_cast("android.content.Intent", chooser.getParcelableExtra(Intent.EXTRA_INTENT))
            _rm_android_probe.share_sequence += 1
            report = {"boot": _rm_android_probe.boot, "sequence": _rm_android_probe.share_sequence,
                "ui_thread": Looper.getMainLooper().equals(Looper.myLooper()),
                "chooser_action": chooser.getAction(), "action": intent.getAction(),
                "mime": intent.getType(), "text": intent.getStringExtra(Intent.EXTRA_TEXT),
                "subject": intent.getStringExtra(Intent.EXTRA_SUBJECT),
                "stream": intent.hasExtra(Intent.EXTRA_STREAM)}
            temporary = _rm_android_probe.directory / "share.tmp"
            temporary.write_text(_rm_android_json.dumps(report, ensure_ascii=False))
            _rm_android_os.replace(temporary, _rm_android_probe.directory / "share.json")
            # Forward the identical observed Intent to the real platform call.
            _rm_android_probe.launch(activity, chooser)

        _rm_android_sharing._launch = _rm_android_share_launch
    else:
        _rm_android_probe.directory = _rm_android_Path(_rm_android_os.environ["RENMODPY_ANDROID_PROBE_DIRECTORY"])
        config.savedir = str(_rm_android_probe.directory / "saves")
    _rm_android_probe.directory.mkdir(parents=True, exist_ok=True)

    def _rm_android_widget_name(widget):
        if isinstance(widget, renpy.display.behavior.Input):
            return "field:" + str(getattr(widget.value, "key", "save_name"))
        if isinstance(widget, renpy.text.text.Text):
            return "".join(part for part in widget.text if isinstance(part, str))
        return "".join(_rm_android_widget_name(child) for child in widget.visit())

    def _rm_android_observe():
        _rm_android_probe.sequence += 1
        screens = [name for name in ("main_menu", "say", "choice", "confirm", "renmodpy_home",
            "renmodpy_records", "renmodpy_settings", "renmodpy_history", "renmodpy_saves",
            "renmodpy_tactics", "renmodpy_validation_tools", "renmodpy_example_media") if renpy.get_screen(name)]
        buttons = []
        for focus in renpy.display.focus.focus_list:
            if focus.x is None:
                continue
            name = _rm_android_widget_name(focus.widget)
            if name:
                buttons.append({"name": name, "rect": [focus.x, focus.y, focus.w, focus.h]})
        input_value, editable = renpy.get_editable_input_value()
        state = {"boot": _rm_android_probe.boot, "sequence": _rm_android_probe.sequence, "android": renpy.android,
            "engine": renpy.version_string, "screens": screens, "buttons": buttons,
            "app_version": config.version,
            "physical_size": renpy.get_physical_size(), "virtual_size": [config.screen_width, config.screen_height],
            "recovery_file": _rm_android_os.path.join(config.savedir, "_reload-1" + renpy.savegame_suffix),
            "main_menu": main_menu, "history": [entry.what for entry in _history_list],
            "font_size": _preferences.font_size, "text_cps": _preferences.text_cps,
            "quick": _rm_services.quick_available(), "resume": _rm_services.resume_slot(),
            "records": _rm_services.records().list(), "saves": _rm_services.save_catalog(),
            "note_result": getattr(renpy.store, "note_result", None),
            "input_text": input_value.get_text() if editable and input_value else None,
            "editable_field": getattr(input_value, "key", "save_name") if editable and input_value else None}
        if renpy.android:
            state["device_orientation"] = int(_rm_android_activity.getResources().getConfiguration().orientation)
            state["ui_callbacks"] = len(_rm_android_jni._ui_calls)
            state["worker_events"] = list(_rm_android_probe.worker_events)
            state["haptic_events"] = list(_rm_android_probe.haptic_events)
        if hasattr(renpy.store, "_rm_validation"):
            state["service_fixture"] = dict(_rm_validation.state)
        if "renmodpy_example_media" in screens:
            texture, fresh = renpy.display.video.get_movie_texture("example_video")
            state["media"] = {"audio_position": renpy.music.get_pos("example_tone"),
                "video_position": renpy.music.get_pos("example_video"), "video_texture": texture is not None}
        state["media_playing"] = {channel: renpy.music.get_playing(channel) for channel in ("example_tone", "example_video")}
        # Validation-only observation of the real SDL/platform clipboard.
        # Production screens read it only when the user requests Paste.
        try:
            state["clipboard"] = _rm_services.clipboard_text()
        except _rm_services.ClipboardError as error:
            state["clipboard_error"] = str(error)
        if "renmodpy_records" in screens:
            form = renpy.get_screen_variable("form", screen="renmodpy_records")
            state["draft"] = dict(form.values)
            state["editing"] = form.editing_id
            state["form_message"] = form.message
            state["transfer"] = dict(renpy.get_screen_variable("transfer", screen="renmodpy_records"))
        temporary = _rm_android_probe.directory / "state.tmp"
        temporary.write_text(_rm_android_json.dumps(state, ensure_ascii=False))
        _rm_android_os.replace(temporary, _rm_android_probe.directory / "state.json")

    config.always_shown_screens.append("renmodpy_android_observer")

screen renmodpy_android_observer():
    zorder 999
    timer 0.3 action Function(_rm_android_observe) repeat True
