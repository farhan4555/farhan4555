# HALO — a 30-second motion-graphics ad

A product spot for **HALO**, a *fictional* smart ring. Everything in it was made with code: no stock footage, no 3D software, no samples.

▶ **Watch:** [`halo-ad.mp4`](halo-ad.mp4) (1920×1080, 30 fps, with sound)

## The edit

| Time | Beat |
|---|---|
| 0–4s | Cold open: a live ECG trace and heartbeat. *"Your body never stops talking. Are you listening?"* |
| 4–6s | Kinetic word hits on the beat: SLEEP. STRESS. RECOVERY. HEART. |
| 6–8s | A vortex of circular type and 900 streaking particles collapses to a point |
| 8–12s | Flash. The ring is revealed with a giant wordmark behind it and text orbiting it in 3D |
| 12–20s | Four feature beats with data viz: heart rate, sleep hypnogram, battery, build |
| 20–24s | Colorways (Titanium, Gold, Midnight, Rose) cut on whip-spins |
| 24–30s | End card: *HALO — Know your body. Available 2027* |

## How it's built

- **`ad.html`**: the whole film as a pure function `renderFrame(t)`.
  - The ring is **raymarched in a GLSL fragment shader**: a signed distance field with machined grooves and inner sensor bumps, metallic Fresnel shading against a procedural studio environment, ambient occlusion, an emissive sensor band, a volumetric glow, and analytic edge anti-aliasing.
  - Typography and data viz are drawn on two Canvas2D layers, one composited *behind* the ring and one *in front*. That's how the orbiting text wraps around the ring in true 3D.
  - A post pass adds bloom, chromatic aberration on impacts, camera shake, a white flash, film grain and a vignette.
  - Open the file in a browser to play it live in real time.
- **`render.js`**: drives headless Chromium frame by frame. It is deterministic, so frames can be rendered in parallel.
- **`gen_audio.py`**: synthesizes the 120 BPM A-minor soundtrack in pure numpy (kicks, claps, hats, saw pads, bass, plucks, risers, impacts, shimmer and the heartbeat), plus convolution reverb. It's timed to the visual cues.

```bash
# render frames (4 workers), make audio, then mux
for w in 0 1 2 3; do node render.js frames 30 0 900 4 $w & done; wait
python3 gen_audio.py halo-audio.wav
ffmpeg -framerate 30 -i frames/f%05d.png -i halo-audio.wav \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest halo-ad.mp4
```
