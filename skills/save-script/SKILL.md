---
name: save-script
description: Save a script from a cloud video editing job (a Modal GPU job, or the ffmpeg/Python steps around it) to the user's private scripts library repo, with notes on what it was used for, so later jobs can reuse it. Use after a job works (or fails instructively), and on "save this script", "add it to the library", "keep this for next time".
---

# Save a script to the library

The library is a private Git repo of past job scripts, with a catalogue (`index.json`) saying what each was used
for. This skill adds to it. Its partner, `find-script`, searches it before a new job is written.

## Preferences

Read `remote-video-editing/preferences.json` under the first data root that exists: `$CLAUDE_USER_DATA`, then
`~/.claude-user-data`, then `${XDG_DATA_HOME:-~/.local/share}/claude-plugins`.

| Key | Default | Meaning |
|-----|---------|---------|
| `scripts_repo` | none | `owner/name` of the library repo on GitHub |
| `scripts_repo_path` | none | Local clone path |

If `scripts_repo` is not set, offer to create one: a **private** repo (`gh repo create <owner>/Cloud-Video-Editing-Scripts --private --clone`),
seeded with a README describing the layout below and `{"schema": 1, "scripts": []}` as `index.json`. Write both keys
into the preferences file. If the clone is missing locally, `gh repo clone` it to `scripts_repo_path`.

## Layout of the library

```
index.json              # catalogue, newest first: the source of truth
scripts/<slug>/         # one folder per job or tool: script files + NOTES.md
```

## Procedure

1. **Pull** the library (`git -C "$LIB" pull -q`).
2. **Decide new or update.** Search `index.json` for an entry with the same purpose. If the script is a revision of
   an existing one, update that folder and entry in place (bump `date`, note what changed in `NOTES.md`). A new slug
   is for a different job only.
3. **Pick the slug:** kebab-case, says what it does, not which video (`sidon-voice-cleanup`, `logo-sting-render`).
4. **Copy the files** that actually ran (Modal app, helper scripts, ffmpeg command files, prompt files for generative
   models) into `scripts/<slug>/`. Then clean them:
   - no secrets, tokens, presigned URLs or session cookies; keys come from the environment;
   - the user's file paths become arguments or clearly named variables;
   - keep the header docstring, and add one if it lacks one: what it does, how to run it, date.
5. **Write `scripts/<slug>/NOTES.md`:** used for (project, video, date), outcome, the exact command and where it ran,
   inputs and outputs, GPU and cost, the wrong turns ruled out, and the part worth reusing.
6. **Add or update the `index.json` entry** at the top of `scripts`: `slug`, `title`, `purpose`, `used_for`, `date`,
   `outcome` (`worked` / `partial` / `failed`), `kind` (`modal` / `ffmpeg` / `python` / `shell` / `mixed`), `files`,
   `entrypoint`, `gpu`, `models`, `inputs`, `outputs`, `cost`, `tags`, `source`, `reuse_notes`. Tags are what a
   later search would type: medium (`audio`, `video`, `image`), operation (`denoise`, `animation`, `upscale`,
   `subtitles`), technique (`chunking`, `two-pass-loudnorm`). Validate with `python3 -m json.tool index.json`.
7. **Commit and push:** `git add -A && git commit -m "Add <slug>: <purpose>" && git push`.
8. Report the slug and the commit in one line.

## Notes

- Save failed attempts too when the lesson is worth keeping (`outcome: failed`, the reason in `NOTES.md`): it stops
  the next job repeating them.
- Large binaries (renders, audio, model weights) never go in the repo. Small fixtures under 1 MB that the script
  needs to run are fine.
