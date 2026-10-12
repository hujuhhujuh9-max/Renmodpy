These original fixtures are generated from FFmpeg's signal/color sources.
They contain no recordings or external artwork and use this repository's
license. `tone.wav` is a two-second, quiet 440 Hz mono PCM tone.
`colors.webm` is silent VP8 video alternating red and blue every 0.75 seconds.

Reproduce with:

```sh
ffmpeg -f lavfi -i 'sine=frequency=440:duration=2:sample_rate=44100' -af volume=0.15 -c:a pcm_s16le tone.wav
ffmpeg -f lavfi -i 'color=c=red:s=320x180:r=20:d=0.75' -f lavfi -i 'color=c=blue:s=320x180:r=20:d=0.75' -filter_complex '[0:v][1:v]concat=n=2:v=1:a=0[v]' -map '[v]' -c:v libvpx -b:v 100k -an colors.webm
```
