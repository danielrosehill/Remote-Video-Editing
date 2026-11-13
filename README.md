# Remote Video Editing

Agent skills for video editing and rendering on rented cloud GPUs ([Modal](https://modal.com)). The local
machine does the light ffmpeg work; the GPU-heavy steps run remotely, so a laptop without a GPU can still
use model-based tools.

## Skills

- `clean-voice-sidon`: clean up a video's voice track with the Sidon v0.1 speech-restoration model on a
  Modal GPU, then two-pass loudness-normalise and remux it without re-encoding the video. Tests on 30 s first.
- `complementary-plugins`: list and install the plugins that go with this one.

## Complementary plugins

- [`video-editing`](https://github.com/danielrosehill/Claude-Video-Editor-Plugin): local editing and
  rendering (Kdenlive, melt, ffmpeg render profiles, silence cutting, subtitles).

## Requirements

- `ffmpeg` locally.
- A Modal account with the CLI set up (`pip install modal` or `uv tool install modal`, then `modal setup`).

## Configuration (optional)

`remote-video-editing/preferences.json` under the first data root that exists: `$CLAUDE_USER_DATA`,
`~/.claude-user-data`, or `${XDG_DATA_HOME:-~/.local/share}/claude-plugins`:

```json
{
  "modal_command": "modal",
  "run_notes": "where and how to run Modal, if not on this machine",
  "loudness_lufs": -14,
  "true_peak_db": -1.5
}
```

## Installation

```bash
claude plugins marketplace add danielrosehill/Claude-Code-Plugins
claude plugins install remote-video-editing@danielrosehill
```
