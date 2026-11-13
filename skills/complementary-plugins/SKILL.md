---
name: complementary-plugins
description: List and install the plugins that complement remote-video-editing, such as video-editing for local Kdenlive, melt and ffmpeg work. Use on "what goes with this plugin", "install the local video plugin", "related plugins".
---

# Complementary plugins

This plugin covers video work that runs on rented cloud GPUs. These plugins cover the rest of the job:

| Plugin | Marketplace | What it adds | Repo |
|--------|-------------|--------------|------|
| `video-editing` | `danielrosehill` | Local editing and rendering: Kdenlive projects, headless `melt` renders, ffmpeg render profiles and transcodes, silence cutting, subtitles, loudness, NAS sync | https://github.com/danielrosehill/Claude-Video-Editor-Plugin |

## Procedure

1. Show the table above. Mark any plugin already installed (`claude plugins list`).
2. For each one the user wants, install it:
   ```bash
   claude plugins marketplace add danielrosehill/Claude-Code-Plugins   # once per machine
   claude plugins install video-editing@danielrosehill
   ```
3. If the user's setup discovers skills on demand instead of installing plugins (a skills catalogue or
   gateway), say so and don't install: search the catalogue for the plugin name instead.

## Typical split

- Cut, arrange and render locally with `video-editing`.
- Send the GPU-heavy steps here: voice cleanup (`clean-voice-sidon`) and, later, other model-based jobs.
- Bring the result back and finish with `video-editing` (`normalize-audio`, `render-with-profile`).
