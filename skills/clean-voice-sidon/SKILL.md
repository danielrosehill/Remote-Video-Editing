---
name: clean-voice-sidon
description: Clean up the voice track of a video (phone or talking-head recording) with the Sidon speech-restoration model on a Modal cloud GPU, then loudness-normalise and remux it into the video. Use on "clean the audio", "enhance my voice", "denoise this video", "fix the phone mic audio".
---

# Clean the voice in a video with Sidon on Modal

Speech restoration with **Sidon v0.1** (`sarulab-speech/sidon-v0.1` on Hugging Face), an audio-to-audio
model that re-synthesises the voice at 48 kHz. It needs a GPU, so the model runs on Modal; everything
else (extracting, loudness, remuxing) is plain ffmpeg on the local machine. The video stream is never
re-encoded.

The Modal job is `scripts/sidon_enhance.py` in this plugin (`${CLAUDE_PLUGIN_ROOT}/scripts/sidon_enhance.py`).

## Model choice (why Sidon)

| Model | Verdict |
|-------|---------|
| Sidon v0.1 | Default. Light; an 11-minute file ran in one job on an L4-class GPU for a few cents. Output is clean, full-band, 48 kHz. |
| NVIDIA RE-USE | Keeps more of the speaker's own spectral detail, but ran out of GPU memory on long files (failed on the second 30 s chunk of an 11-minute file). Use only for short clips. |
| DeepFilterNet | Ruled out: audible distortion on voice. |

Sidon regenerates everything above 8 kHz, so the result is a voice with no room or background left in it.
Music and other non-speech sound in the track are lost. If the video has music beds, clean the voice
before adding them.

## Preferences

Read `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/remote-video-editing/preferences.json` if it exists:

| Key | Default | Meaning |
|-----|---------|---------|
| `modal_command` | `modal` | Command that runs Modal apps (a wrapper that selects a profile or workspace is fine) |
| `run_notes` | none | Free-text instructions on *where* to run Modal (e.g. another host that holds the auth) and how files reach it. Follow them. |
| `loudness_lufs` | `-14` | Integrated loudness target (YouTube-style) |
| `true_peak_db` | `-1.5` | True-peak ceiling |

If no file exists and `modal token` is not set up (`modal profile current` fails), stop and tell the user
to run `modal setup` first.

## Procedure

Work in a folder next to the source video. `IN=<video>`, `MODAL=<modal_command, default modal>`.

1. **Extract the audio** as mono 48 kHz FLAC:
   ```bash
   ffmpeg -v error -y -i "$IN" -vn -ac 1 -ar 48000 -c:a flac -sample_fmt s16 audio.flac
   ```
2. **Test on 30 seconds first.** Cut a clip from a section with speech (not the first seconds):
   ```bash
   ffmpeg -v error -y -ss 60 -t 30 -i audio.flac -c:a flac test30.flac
   $MODAL run "${CLAUDE_PLUGIN_ROOT}/scripts/sidon_enhance.py" --src test30.flac --out test30_sidon.flac
   ```
   Hand both files to the user to listen to. Do not run the full file until they approve the sound.
3. **Run the full track:**
   ```bash
   $MODAL run "${CLAUDE_PLUGIN_ROOT}/scripts/sidon_enhance.py" --src audio.flac --out audio_sidon.flac
   ```
   The job prints one line per 96 s chunk. The first run builds the image (a few minutes); later runs reuse it.
4. **Measure loudness** (first pass of two-pass `loudnorm`):
   ```bash
   ffmpeg -hide_banner -nostats -i audio_sidon.flac \
     -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | grep -A12 '^{'
   ```
5. **Remux** with the measured values. The video is stream-copied:
   ```bash
   ffmpeg -v error -y -i "$IN" -i audio_sidon.flac -map 0:v -map 1:a -c:v copy \
     -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=<input_i>:measured_TP=<input_tp>:measured_LRA=<input_lra>:measured_thresh=<input_thresh>:offset=<target_offset>:linear=true,aresample=48000" \
     -c:a aac -b:a 192k -movflags +faststart "<name>_clean.mp4"
   ```
   For HEVC sources that must play in Apple players, add `-tag:v hvc1`.
6. **Verify:** `ffprobe` the duration against the source (should match to within a frame), and cut a 30 s
   before/after pair at the same offset (`-vn -c:a copy`) for the user to compare.

## Cost and limits

- GPU list in the script: L4, A10G, L40S (whichever Modal has free). Timeout 1 hour.
- The whole file is sent to the function as bytes. Fine for voice tracks up to an hour or two of mono FLAC;
  for longer material, split the audio, run the parts, and join them with ffmpeg `concat`.
- Weights download from Hugging Face on each cold start (public, no token needed).

## Related

For local editing, rendering and audio work (Kdenlive, melt, ffmpeg presets, silence cutting), see the
`complementary-plugins` skill in this plugin.
