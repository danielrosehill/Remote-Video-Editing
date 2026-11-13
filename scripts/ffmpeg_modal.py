"""Run one ffmpeg render on a Modal CPU container: long encodes (intro/outro joins, re-encodes, landscape cuts).

Part of the remote-video-editing plugin (skills add-intro-outro and any full-length re-encode). The inputs are pushed
to a Modal Volume once (re-runs reuse them), ffmpeg runs in a 16-core container, and the output is pulled back.

    modal run ffmpeg_modal.py --inputs "intro.mp4,main.mp4,outro.mp4" --args-file render.args --out final.mp4

`render.args` holds the ffmpeg arguments between the inputs and the output, one per line (so a filter graph with
spaces and quotes needs no shell escaping), e.g. `-filter_complex` / `<graph>` / `-map` / `[v]` / ... . Inputs are
given to ffmpeg in the order listed as `-i` options. Cost: CPU containers are billed per core-second; a 13-minute
1080p x264 medium encode is roughly ten minutes on 16 cores (a few tens of cents at most).
"""
import pathlib
import modal

app = modal.App("ffmpeg-render")
image = modal.Image.debian_slim(python_version="3.12").apt_install("ffmpeg")
vol = modal.Volume.from_name("ffmpeg-render-work", create_if_missing=True)


@app.function(image=image, cpu=16, memory=16384, timeout=3 * 3600, volumes={"/work": vol})
def render(job: str, names: list[str], args: list[str], out_name: str) -> str:
    import subprocess
    vol.reload()
    d = pathlib.Path("/work") / job
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats"]
    for n in names:
        cmd += ["-i", str(d / n)]
    cmd += args + [str(d / out_name)]
    subprocess.run(cmd, check=True)
    vol.commit()
    return f"{job}/{out_name}"


@app.local_entrypoint()
def main(inputs: str, args_file: str, out: str, job: str = ""):
    import hashlib, subprocess
    paths = [pathlib.Path(p) for p in inputs.split(",")]
    job = job or hashlib.sha1(("|".join(p.name for p in paths) + out).encode()).hexdigest()[:10]
    existing = {e.path for e in vol.listdir(job)} if job in {e.path for e in vol.listdir("/")} else set()
    with vol.batch_upload(force=True) as b:
        for p in paths:
            if f"{job}/{p.name}" not in existing:
                b.put_file(str(p), f"/{job}/{p.name}")
    args = [l for l in pathlib.Path(args_file).read_text().splitlines() if l.strip()]
    remote = render.remote(job, [p.name for p in paths], args, pathlib.Path(out).name)
    with open(out, "wb") as f:
        for chunk in vol.read_file(remote):
            f.write(chunk)
    print(f"wrote {out}; inputs stay in volume ffmpeg-render-work/{job} (delete with: modal volume rm -r ffmpeg-render-work {job})")
