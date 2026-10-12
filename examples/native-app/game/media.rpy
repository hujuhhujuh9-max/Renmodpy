# Ordinary Ren'Py audio, Movie and ATL: no additional rendering/runtime owner.
define renmodpy_home_links = (("Media room", "renmodpy_example_media"),)

init python:
    renpy.music.register_channel("example_tone", mixer="music", loop=True)
    renpy.music.register_channel("example_video", mixer="movie", loop=True, movie=True)

transform renmodpy_example_motion:
    xpos 70
    ypos 1000
    linear 0.8 xpos 550
    linear 0.8 xpos 70
    repeat

screen renmodpy_example_media():
    tag menu
    style_prefix "renmodpy"
    add Solid("#101d27")
    on "show" action Play("example_tone", "media/tone.wav", loop=True)
    on "replace" action Play("example_tone", "media/tone.wav", loop=True)
    on "hide" action Stop("example_tone")
    on "replaced" action Stop("example_tone")
    vbox:
        xpos 36
        ypos 44
        xsize 648
        spacing 20
        text "Media room" style "renmodpy_heading"
        text "A quiet tone, a looping video and a moving light." style "renmodpy_caption"
        textbutton "Stop tone" action Stop("example_tone")
        textbutton "Play tone" action Play("example_tone", "media/tone.wav", loop=True)
        textbutton "Home" action ShowMenu("renmodpy_home")
    add Movie(size=(600, 338), channel="example_video", play="media/colors.webm", loop=True):
        xpos 60
        ypos 450
    text "Native ATL animation" xpos 36 ypos 900 style "renmodpy_caption"
    add Solid("#60d9ef", xsize=80, ysize=60) at renmodpy_example_motion
    key "game_menu" action ShowMenu("renmodpy_home")
