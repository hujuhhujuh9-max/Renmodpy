define config.name = "RenModPy Native Example"
define config.version = "0.1.0"
define config.save_directory = "renmodpy-native-example"
define config.screen_width = 720
define config.screen_height = 1280
define config.default_text_cps = 30
define config.game_menu_action = ShowMenu("renmodpy_home")
define config.history_length = 100
define build.name = "renmodpy_native_example"
define narrator = Character(None)

screen main_menu():
    tag menu
    use renmodpy_home()

screen confirm(message, yes_action, no_action):
    modal True
    zorder 200
    style_prefix "renmodpy"
    add Solid("#101d27e8")
    frame:
        xalign 0.5
        yalign 0.5
        xsize 640
        vbox:
            spacing 30
            text message
            hbox:
                spacing 24
                textbutton "Yes" action [Hide("confirm"), yes_action]
                textbutton "No" action [Hide("confirm"), no_action]
    key "game_menu" action [Hide("confirm"), no_action]

screen say(who, what):
    add Solid("#152c39")
    window:
        id "window"
        xpos 24
        ypos 780
        xanchor 0
        yanchor 0
        xsize 672
        ysize 380
        background Solid("#203f4d")
        padding (26, 30)
        vbox:
            spacing 20
            if who:
                text who id "who" size 30 color "#91d4d5"
            text what id "what" size 32 color "#e9f1f4"
    textbutton "Home":
        style_prefix "renmodpy"
        xpos 36
        ypos 44
        action [Function(_rm_return_home), ShowMenu("renmodpy_home")]
    key "game_menu" action [Function(_rm_return_home), ShowMenu("renmodpy_home")]

screen choice(items):
    style_prefix "renmodpy"
    add Solid("#152c39")
    vbox:
        xpos 36
        ypos 340
        xsize 648
        spacing 24
        text "The lighthouse note" style "renmodpy_heading"
        for item in items:
            textbutton item.caption action item.action xfill True
        textbutton "Home" action [Function(_rm_return_home), ShowMenu("renmodpy_home")]
    key "game_menu" action [Function(_rm_return_home), ShowMenu("renmodpy_home")]

label start:
    $ _rm_services.begin_story()
    $ renmodpy_scene = "The lighthouse"
    narrator "Someone left a folded note at the lighthouse. The tide returns before sunset."
    menu:
        "Keep a copy":
            $ note_result = "You kept a copy of the lighthouse note."
        "Share it with Mira":
            $ note_result = "You shared the lighthouse note with Mira."
    narrator "[note_result]"
    $ renmodpy_scene = "The balcony route"
    call renmodpy_tactics from native_app_tactics_return
    if _return == "reached":
        narrator "The Scout reached the balcony before the light faded."
    else:
        narrator "You left the balcony route for another evening."
    $ _rm_services.finish_story(note_result)
    return
