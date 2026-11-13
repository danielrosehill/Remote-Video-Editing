---
name: add-intro-outro
description: Put the user's brand intro and outro stings on a finished video (with optional vid.stab stabilisation for handheld phone footage), choosing the 16:9 or 9:16 pair to match the video's orientation, with a short fade from the intro into the video and from the video into the outro. Also builds a 16:9 cut of a vertical video with a blurred background. Use on "add the intro", "put the intro and outro on", "brand the video", "make a landscape version", "final render for YouTube".
---

# Add the intro and outro

The stings are short MP4s with their own jingle, one pair per orientation, listed in preferences. This skill
normalises everything to one format, joins intro, video and outro with short cross-fades (video and audio), and
renders the result.

## Preferences

`remote-video-editing/preferences.json` (lookup order as in `clean-voice-sidon`):

| Key | Meaning |
|-----|---------|
| `stings` | `{"intro_16x9": url, "outro_16x9": url, "intro_9x16": url, "outro_9x16": url}`; URLs or local paths |
| `sting_fade_s` | Cross-fade length, default `0.5` |
| `render_notes` | Where to run long encodes (e.g. a server rather than a laptop). Follow them. |

If `stings` is not set, ask for the files. The plugin does not ship any brand assets.

## Orientation

Read the **displayed** orientation, not the coded size: phones store portrait video as 1920x1080 with a rotation
tag. Check with
`ffprobe -v error -select_streams v:0 -show_entries stream=width,height:stream_side_data=rotation -of compact IN`.
A rotation of 90 or -90 swaps width and height. ffmpeg applies the rotation automatically when it decodes.

- Portrait (9:16) video: use `intro_9x16` / `outro_9x16`, canvas 1080x1920.
- Landscape: use the 16:9 pair, canvas 1920x1080.
- **16:9 cut of a portrait video** (for YouTube's main feed): canvas 1920x1080, the video scaled to 1080 high in the
  centre, over a blurred, darkened, zoomed copy of itself; use the 16:9 stings. The `[v1]` chain below becomes:
  ```
  [1:v]fps=30,split[a][b];
  [a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,scale=480:270,boxblur=20:2,scale=1920:1080,eq=brightness=-0.06:saturation=0.9[bg];
  [b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0,setsar=1,format=yuv420p[v1]
  ```
  Test it on an 8-second cut (`-ss 60 -t 8`) and show a frame before rendering the whole thing.

## Render

`W:H` is the canvas, `F` the fade (0.5), `DI` the intro duration, `DV` the video duration (ffprobe `format=duration`).
Offsets: first fade at `DI-F`; second at `DI+DV-2*F`.

```bash
ffmpeg -y -i intro.mp4 -i main.mp4 -i outro.mp4 -filter_complex "
 [0:v]fps=30,scale=W:H,setsar=1,format=yuv420p[v0];
 [1:v]fps=30,scale=W:H:force_original_aspect_ratio=decrease,pad=W:H:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[v1];
 [2:v]fps=30,scale=W:H,setsar=1,format=yuv420p[v2];
 [0:a]aresample=48000,aformat=channel_layouts=stereo[a0];
 [1:a]aresample=48000,aformat=channel_layouts=stereo[a1];
 [2:a]aresample=48000,aformat=channel_layouts=stereo[a2];
 [v0][v1]xfade=transition=fade:duration=F:offset=DI-F[v01];
 [v01][v2]xfade=transition=fade:duration=F:offset=DI+DV-2*F[v];
 [a0][a1]acrossfade=d=F[a01];[a01][a2]acrossfade=d=F[a]" \
 -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -movflags +faststart out.mp4
```

- Several source clips: join them first (same filter pattern, or the concat demuxer if they share a codec), then
  treat the result as `main.mp4`.
- This is a full re-encode: minutes of every core for a 10-minute 1080p video. **Run it on Modal**, not locally and
  not on a home server: put the arguments after the inputs (from `-filter_complex` to `+faststart`) one per line in
  `render.args`, then
  `$MODAL run "${CLAUDE_PLUGIN_ROOT}/scripts/ffmpeg_modal.py" --inputs intro.mp4,main.mp4,outro.mp4 --args-file render.args --out out.mp4`
  (`modal_command` and `run_notes` from preferences say where Modal runs). Join several clips in the same graph
  (`concat` filter) rather than as a separate pass. Delete the job's folder in volume `ffmpeg-render-work` afterwards.
- xfade needs both inputs on the same timebase: put `fps=30,settb=1/30` on every video branch (including after a
  `concat`), or ffmpeg fails with "First input link main timebase (1/30) do not match".
- Verify: output duration is about `DI + DV + DO - 2*F`, and check frames at `DI-F/2` (mid-fade), the middle and
  the end.

## Handheld footage: stabilise in the same render

Phone videos shot handheld benefit from light stabilisation (Daniel, 2026-11-13, after the first Hebrish weekend
update went out without it). Use ffmpeg's vid.stab (`libvidstab`; Debian's ffmpeg, which the Modal image installs,
has it; check with `ffmpeg -filters | grep vidstab`). Two passes, both on Modal:

1. **Detect** (fast, analysis only, writes a transforms file), per source clip:
   `ffmpeg -i main.mp4 -vf vidstabdetect=shakiness=5:accuracy=15:result=main.trf -f null -`
   Run it as its own `ffmpeg_modal.py` job (args `-vf` / `vidstabdetect=...:result=/work/<job>/main.trf` / `-f` /
   `null`, output `-`), or add a detect step to the script. The `.trf` must sit beside the input in the volume.
2. **Transform** inside the main render, first thing on that clip's video branch, before grade and scale:
   `vidstabtransform=input=main.trf:smoothing=20:zoom=2:optzoom=0,unsharp=5:5:0.4`
   `smoothing` around 15-30 (frames) keeps natural motion; a fixed `zoom=2` (percent) hides the moving borders
   without the pumping `optzoom=1` causes on a talking head. The light unsharp offsets the resampling softness.

Test on an 8-second cut first and compare a still and a short clip with the user before the full render. If
`libvidstab` is missing, `deshake` is a one-pass fallback (weaker). AI stabilisers are not needed for this.

## Making stings

The stings in use were rendered from the brand SVGs with a small Pillow script plus a generated jingle. Find it
with `find-script` (tags `logo`, `sting`, `intro`), and don't regenerate the logo with a video model: video models
distort letterforms.
