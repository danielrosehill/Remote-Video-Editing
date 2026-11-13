"""Clean up the voice in a recording with Sidon v0.1 (sarulab-speech/sidon-v0.1) on a Modal GPU.

Part of the remote-video-editing plugin, skill clean-voice-sidon. Chain follows the model authors' demo Space:
peak-normalize to 0.9, 50 Hz high-pass, 16 kHz w2v-BERT 2.0 features in 96 s chunks (one-frame cache across chunk
boundaries), vocoder at 48 kHz. Sidon regenerates everything above 8 kHz, so the output is a clean re-synthesis of
the voice, not a filtered copy.

    modal run sidon_enhance.py --src in.flac --out in_sidon.flac

Input: any file soundfile reads (FLAC/WAV), mixed to mono. Output: 48 kHz mono FLAC, 24-bit.
Loudness and remuxing into the video are done afterwards with ffmpeg (light work, any machine).
First validated 2026-11-13 on an 11-minute phone recording (L4 class GPU, a few cents).
"""
import io
from pathlib import Path

import modal

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libsndfile1")
    .pip_install("torch==2.8.0", "torchaudio==2.8.0", "transformers>=4.45", "huggingface_hub>=0.34", "soundfile", "numpy")
)
app = modal.App("sidon-voice-enhance", image=image)


@app.function(gpu=["L4", "A10G", "L40S"], timeout=3600)
def enhance(audio: bytes) -> bytes:
    import numpy as np, soundfile as sf, torch, torchaudio, transformers
    from huggingface_hub import hf_hub_download

    fe = torch.jit.load(hf_hub_download("sarulab-speech/sidon-v0.1", "feature_extractor_cuda.pt"), map_location="cuda")
    dec = torch.jit.load(hf_hub_download("sarulab-speech/sidon-v0.1", "decoder_cuda.pt"), map_location="cuda")
    pre = transformers.SeamlessM4TFeatureExtractor.from_pretrained("facebook/w2v-bert-2.0")

    wav, sr = sf.read(io.BytesIO(audio), dtype="float32", always_2d=True)
    wav = wav.mean(axis=1)
    with torch.inference_mode():
        x = torch.tensor(0.9 * wav / np.abs(wav).max(), dtype=torch.float32).view(1, -1)
        n = int(48_000 / sr * x.shape[1])
        x = torchaudio.functional.highpass_biquad(x, sr, 50)
        w16 = torch.nn.functional.pad(torchaudio.functional.resample(x, sr, 16_000), (0, 24000))
        out, cache = [], None
        for i, chunk in enumerate(w16.view(-1).split(16000 * 96)):
            feats = pre(torch.nn.functional.pad(chunk, (160, 160)), return_tensors="pt", sampling_rate=16000)
            f = fe(feats["input_features"].to("cuda"))["last_hidden_state"]
            if cache is not None:
                f = torch.cat([cache, f], dim=1)
            out.append(dec(f.transpose(1, 2)).view(-1)[:-960].cpu())
            cache = f[:, -1:]
            print(f"chunk {i}: {i * 96}s", flush=True)
        y = torch.cat(out).numpy()[:n]
    b = io.BytesIO()
    sf.write(b, y, 48_000, format="FLAC", subtype="PCM_24")
    return b.getvalue()


@app.local_entrypoint()
def main(src: str, out: str = ""):
    out = out or str(Path(src).with_name(Path(src).stem + "_sidon.flac"))
    Path(out).write_bytes(enhance.remote(Path(src).read_bytes()))
    print("wrote", out)
