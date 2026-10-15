"""Generate the listening audio files with Kokoro-82M (Apache-2.0), voices ef_dora (woman) and em_alex (man).

Usage (from repo root):  python3 src/dele-a2/make_audio.py MODEL.onnx VOICES.npz TEST_NUMBERS...
  e.g.  python3 src/dele-a2/make_audio.py kokoro-q8.onnx voices_es.npz 1 2 3
Writes dele-a2/audio/L{n}/{key}.mp3, where key is "a{item number}" or "t3" (task 3 conversation).
Model: npm package kokoro-q8-shards (concatenate the 6 parts). Voices: npm package kokoro-js, voices/*.bin
(float32, 510x256), saved as an .npz with arrays shaped (510,1,256).
"""
import json, os, re, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SRC))
VOICE = {"M": "ef_dora", "H": "em_alex"}
SPEED = 0.95
SR = 24000

FIX = [  # spell out codes and numbers the way a Spanish announcer reads them
    (r"\bIB 3170\b", "I be treinta y uno setenta"), (r"\bB 22\b", "be veintidós"), (r"\bC 14\b", "ce catorce"),
    (r"\bC 8\b", "ce ocho"), (r"\b18:45\b", "dieciocho cuarenta y cinco"), (r"\b2345\b", "dos tres cuatro cinco"),
    (r"\b4521\b", "cuatro cinco dos uno"), (r"\b010\b", "cero diez"), (r"\bDNI\b", "de ene i"),
]
FEMALE_SPK = re.compile(r"\bsoy (Clara|Marta|la profesora|la doctora)\b", re.I)
MALE_SPK = re.compile(r"\bsoy (Pedro|Luis|Andrés)\b", re.I)

def norm(t):
    for a, b in FIX: t = re.sub(a, b, t)
    return t

def silence(sec): return np.zeros(int(SR * sec), dtype=np.float32)

def narrator(text, idx):
    if FEMALE_SPK.search(text): return "ef_dora"
    if MALE_SPK.search(text): return "em_alex"
    return "ef_dora" if idx % 2 == 0 else "em_alex"

def render(k, lines, out):
    parts = [silence(0.4)]; prev = None
    for voice, text in lines:
        if prev is not None: parts.append(silence(0.3 if voice == prev else 0.55))
        a, sr = k.create(norm(text), voice=voice, speed=SPEED, lang="es"); assert sr == SR
        parts.append(a.astype(np.float32)); prev = voice
    parts.append(silence(0.5))
    wav = np.concatenate(parts); peak = float(np.max(np.abs(wav))) or 1.0
    wav = wav / peak * 0.89
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f: tmp = f.name
    sf.write(tmp, wav, SR)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-ac", "1", "-ar", "24000", "-b:a", "48k", out], check=True)
    os.remove(tmp)
    return len(wav) / SR

def main():
    model, voices, nums = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3:]]
    k = Kokoro(model, voices)
    for n in nums:
        d = json.load(open(os.path.join(SRC, f"L{n}.json"))); T = {t["t"]: t for t in d["tasks"]}
        od = os.path.join(ROOT, "dele-a2", "audio", f"L{n}"); os.makedirs(od, exist_ok=True)
        jobs = []; num = 0
        for i, it in enumerate(T[1]["items"]):
            num += 1; jobs.append((f"a{num}", [(VOICE[r], s) for r, s in it["s"]]))
        for i, it in enumerate(T[2]["items"]):
            num += 1; jobs.append((f"a{num}", [(narrator(s, i), s) for r, s in it["s"]]))
        jobs.append(("t3", [(VOICE[r], s) for r, s in T[3]["s"]])); num += 6
        for i, m in enumerate(T[4]["msgs"]):
            num += 1; jobs.append((f"a{num}", [(narrator(s, i + 1), s) for r, s in m["s"]]))
        for key, lines in jobs:
            out = os.path.join(od, f"{key}.mp3")
            if os.path.exists(out) and os.path.getsize(out) > 1000: continue
            dur = render(k, lines, out)
            print(f"L{n} {key} {dur:.1f}s", flush=True)
    print("DONE", nums, flush=True)

if __name__ == "__main__":
    main()
