---
name: find-script
description: Search the user's private library of past cloud video editing scripts (Modal GPU jobs, ffmpeg and Python steps) for one to reuse or adapt before writing a new one, and say which, why and what to change. Use before writing any new video or audio processing script, and on "have we done this before", "check the script library", "is there a script for X", "reuse the old code".
---

# Find a script to reuse

Before writing a new job script, check whether a past one already does it, or most of it. The library and its
catalogue are described in the `save-script` skill.

## Preferences

`scripts_repo` and `scripts_repo_path` from `remote-video-editing/preferences.json` (same lookup order as
`save-script`). If they are not set, say there is no library yet and carry on writing the script; offer
`save-script` afterwards.

## Procedure

1. **Pull** the library: `git -C "$LIB" pull -q` (clone it with `gh repo clone` if the path is missing).
2. **Search the catalogue** first, not the code. Turn the task into terms (medium, operation, model, technique) and
   match them against `title`, `purpose`, `tags`, `models` and `reuse_notes` in `index.json`:
   ```bash
   jq -r '.scripts[] | [.slug, .outcome, .date, .purpose, (.tags|join(","))] | @tsv' "$LIB/index.json"
   ```
   Then grep the code for the specific call if the catalogue is not enough (`grep -rn "loudnorm\|gpu=" "$LIB/scripts"`).
   An empty search on a library that should have a match is a suspect search: try synonyms (`denoise` / `enhance` /
   `restore`) before concluding there is nothing.
3. **Read the candidates' `NOTES.md` and script**, at most the top three.
4. **Decide and say so in one or two lines:**
   - **Reuse:** it does the job as is. Give the command from `entrypoint` with the new inputs.
   - **Adapt:** it does most of it. Copy it into the working folder, name the changes (model, chunk size, output
     format), and keep its header crediting the slug it came from.
   - **Write fresh:** nothing fits. Name the nearest entry and what is worth borrowing from it (`reuse_notes`).
   Check `outcome`: a `failed` entry is a warning about what not to do, not a starting point.
5. After the job, run `save-script`: update the entry if it was reused or adapted (new `used_for` line in
   `NOTES.md`), or add a new one.
