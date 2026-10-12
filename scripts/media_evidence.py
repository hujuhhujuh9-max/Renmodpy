"""Check visible decoded colors and motion in native/emulator screenshots."""
from pathlib import Path
from PIL import Image


def inspect_frames(paths):
    samples = []
    for path in paths:
        with Image.open(path) as source:
            image = source.convert("RGB").resize((720, 1280))
        red, green, blue = image.getpixel((360, 620))
        color = "red" if red > 180 and blue < 70 else "blue" if blue > 180 and red < 70 else "other"
        lights = [x for x in range(720) if all(abs(value - target) < 20 for value, target in
                  zip(image.getpixel((x, 1030)), (96, 217, 239)))]
        if not lights:
            raise AssertionError("The animated light is absent from " + str(path))
        samples.append({"frame": Path(path).name, "video_color": color, "light_x": sum(lights) / len(lights)})
    assert {sample["video_color"] for sample in samples} >= {"red", "blue"}, samples
    assert max(sample["light_x"] for sample in samples) - min(sample["light_x"] for sample in samples) > 100, samples
    return samples
