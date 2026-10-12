# Disposable driver for the ordinary example screen and native media channels.
init 900 python:
    import json as _rm_media_json
    import os as _rm_media_os
    from pathlib import Path as _rm_media_Path
    config.label_overrides["start"] = "renmodpy_check_media"

label renmodpy_check_media:
    show screen renmodpy_home
    show screen renmodpy_example_media
    $ _rm_media_positions = []
    $ _rm_media_output = _rm_media_Path(_rm_media_os.environ["RENMODPY_CHECK_OUTPUT"])
    $ renpy.pause(0.5, hard=True)
    python:
        for index in range(6):
            renpy.pause(0.35, hard=True)
            _rm_media_positions.append(renpy.music.get_pos("example_tone"))
            texture, fresh = renpy.display.video.get_movie_texture("example_video")
            assert texture is not None
            assert renpy.screenshot(str(_rm_media_output / ("media-%d.png" % index)))
        assert all(position is not None for position in _rm_media_positions)
        assert len(set(round(position, 2) for position in _rm_media_positions)) > 1
    show screen renmodpy_home
    $ renpy.pause(0.3, hard=True)
    python:
        assert renpy.music.get_playing("example_tone") is None
        assert renpy.music.get_playing("example_video") is None
        (_rm_media_output / "media-passed.json").write_text(_rm_media_json.dumps({
            "result": "passed", "audio_positions": _rm_media_positions,
            "video_texture": True, "channels_stop_on_exit": True,
            "physical_audio_verified": False}, indent=2) + "\n")
        renpy.quit()
