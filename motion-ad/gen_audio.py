"""Synthesizes the 30 s HALO soundtrack (120 BPM, A minor), timed to the visual cues in ad.html.
Pure numpy — no samples. Writes halo-audio.wav."""
import numpy as np, wave, sys

SR = 44100
DUR = 30.0
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(3)
BEAT = 0.5


def t_(d): return np.arange(int(d * SR)) / SR


def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N: return
    sig = sig[: N - i]
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    L[i:i + len(sig)] += sig * gain * l * 1.414
    R[i:i + len(sig)] += sig * gain * r * 1.414


def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(f)
    if hi: g *= 1 / np.sqrt(1 + (f / hi) ** 4)
    if lo: g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X * g, len(x))


def env(n, a, d, sus=0.0):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * (sus + (1 - sus) * np.exp(-t / d))


def osc(freq, d, kind='sin', phase=0.0):
    t = t_(d)
    ph = 2 * np.pi * np.cumsum(np.broadcast_to(freq, t.shape)) / SR + phase
    if kind == 'sin': return np.sin(ph)
    if kind == 'saw':  # mildly band-limited saw via a few harmonics
        f0 = float(np.mean(freq)); k = int(min(30, 16000 / f0))
        return sum(np.sin(ph * h) / h for h in range(1, k + 1)) * 0.6
    if kind == 'tri': return 2 / np.pi * np.arcsin(np.sin(ph))


def noise(d): return rng.standard_normal(int(d * SR))


# ---------- instruments ----------
def kick(big=False):
    d = 1.2 if big else 0.45; t = t_(d)
    f = 42 + (150 if big else 120) * np.exp(-t * (18 if big else 28))
    s = osc(f, d) * env(len(t), 0.001, 0.5 if big else 0.18)
    click = fft_filter(noise(0.01), lo=2000) * 0.4
    s[:len(click)] += click
    return np.tanh(s * 1.6)


def heartbeat():
    def thump(g, d=0.22):
        t = t_(d); f = 38 + 30 * np.exp(-t * 25)
        return osc(f, d) * env(len(t), 0.004, 0.06) * g
    s = np.zeros(int(0.6 * SR)); a = thump(1.0); b = thump(0.65)
    s[:len(a)] += a; j = int(0.2 * SR); s[j:j + len(b)] += b
    return np.tanh(s * 2.2) * 0.9


def clap():
    n = fft_filter(noise(0.35), lo=900, hi=7000)
    e = np.zeros_like(n); t = np.arange(len(n)) / SR
    for k, o in enumerate([0, 0.011, 0.022]):
        e += np.where(t >= o, np.exp(-(t - o) / (0.008 if k < 2 else 0.12)), 0)
    return n * e * 0.5


def hat(open_=False):
    d = 0.25 if open_ else 0.06
    return fft_filter(noise(d), lo=7000) * env(int(d * SR), 0.001, 0.08 if open_ else 0.018) * 0.5


def impact(size=1.0):
    d = 3.5; out = np.zeros(int(d * SR))
    k = kick(True); out[:len(k)] += k * 1.1
    boom = fft_filter(noise(d), hi=180) * env(int(d * SR), 0.005, 0.6) * 2.5
    sub = osc(36 + 20 * np.exp(-t_(d) * 3), d) * env(int(d * SR), 0.01, 1.1) * 0.9
    crack = fft_filter(noise(0.6), lo=1500, hi=9000) * env(int(0.6 * SR), 0.001, 0.09) * 0.7
    out += boom + sub; out[:len(crack)] += crack
    return np.tanh(out * size)


def shimmer(d=3.0):
    t = t_(d); s = np.zeros_like(t)
    for f in [1760, 2217.5, 2637, 3520, 4434]:
        s += np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-t * (1.2 + f / 3000))
    return s * 0.08 * np.minimum(1, t / 0.01)


def riser(d, f0=200, f1=1600):
    t = t_(d); x = t / d
    n = fft_filter(noise(d), lo=500) * x ** 2.5 * 0.5
    tone = osc(f0 * (f1 / f0) ** (x ** 1.5), d, 'saw') * x ** 2 * 0.12
    return n + fft_filter(tone, hi=5000)


def reverse_swell(d):
    s = fft_filter(noise(d), lo=300, hi=6000) * np.linspace(0, 1, int(d * SR)) ** 3
    return s * 0.45


def whoosh(d=0.5):
    x = np.linspace(0, 1, int(d * SR)); e = np.sin(np.pi * x) ** 2
    return fft_filter(noise(d), lo=400, hi=5000) * e * 0.55


def pad(freqs, d, gain=0.1, bright=1800):
    s = np.zeros(int(d * SR))
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            s += osc(f * 2 ** (det / 12), d, 'saw', rng.random() * 6)
    s = fft_filter(s, hi=bright)
    x = np.arange(len(s)) / SR
    e = np.minimum(1, x / 0.6) * np.minimum(1, (d - x) / 0.6)
    return s * e * gain / len(freqs)


def bass(f, d):
    s = osc(f, d, 'saw') * 0.6 + osc(f / 2, d) * 0.8
    s = fft_filter(s, hi=380)
    return np.tanh(s * env(len(s), 0.004, 0.25, 0.35) * 1.5) * 0.55


def pluck(f, d=0.35):
    s = osc(f, d, 'tri') + 0.3 * osc(f * 2, d)
    return fft_filter(s * env(len(s), 0.002, 0.09), hi=5000) * 0.18


# ---------- arrangement ----------
A2, C3, D3, E3, F2, G2 = 110.0, 130.81, 146.83, 164.81, 87.31, 98.0
CHORDS = [(A2, [220, 261.63, 329.63]), (F2, [174.61, 220, 261.63]),
          (C3 / 2 * 2, [196, 261.63, 329.63]), (G2, [196, 246.94, 293.66])]

# 0–4: heartbeat cold open
for b in [0.55, 1.55, 2.55, 3.4]: add(heartbeat(), b, 1.0)
add(pad([55, 110, 164.8], 4.2, 0.07, 500), 0.0)
add(reverse_swell(1.0), 3.0, 0.9)

# 4–6: word hits
for k, b in enumerate([4.0, 4.5, 5.0, 5.5]):
    add(kick(), b, 1.0); add(clap(), b, 0.6, (-.3, .3, -.2, .2)[k])
    add(bass([A2, A2, F2, G2][k], 0.45), b, 0.9)
add(impact(0.7), 4.0, 0.6)

# 6–8: vortex build
add(pad([220, 261.63, 329.63, 440], 2.2, 0.09, 2500), 6.0)
for i in range(16): add(hat(), 6.0 + i * 0.125, 0.5 + 0.03 * i, 0.4 * np.sin(i))
add(riser(1.6), 6.4, 1.0)
t = 7.0; step = 0.125
while t < 7.98:
    add(clap(), t, 0.25 + 0.5 * (t - 7.0)); t += step; step = max(0.03, step * 0.82)

# 8: reveal
add(impact(1.0), 8.0, 1.1); add(shimmer(3.5), 8.0, 1.0)
add(pad([110, 220, 261.63, 329.63, 493.88], 4.0, 0.12, 2400), 8.0)

# 10–24: groove
for bar in range(10, 24, 2):
    root, ch = CHORDS[((bar - 10) // 2) % 4]
    add(pad(ch, 2.05, 0.08, 2200), bar)
    for k in range(4):
        b = bar + k * BEAT
        if b >= 24: break
        add(kick(), b, 0.95)
        add(hat(), b + 0.25, 0.55, 0.25); add(hat(), b + 0.125, 0.18, -0.3); add(hat(), b + 0.375, 0.18, 0.3)
        if k % 2: add(clap(), b, 0.5)
        add(bass(root if k != 3 else root * 1.5, 0.24), b, 0.8); add(bass(root, 0.2), b + 0.25, 0.55)
    arp = ch + [ch[0] * 2, ch[1] * 2]
    for k in range(16):
        b = bar + k * 0.125
        if b >= 24: break
        add(pluck(arp[(k * 3) % len(arp)] * 2), b, 0.55 if k % 4 == 0 else 0.35, 0.5 * np.sin(k * 1.3))
for b in [12, 14, 16, 18]: add(whoosh(0.35), b - 0.3, 0.35, 0.4)
for b in [20, 21, 22, 23]:
    add(whoosh(0.5), b - 0.25, 0.9); add(impact(0.5), b, 0.35); add(shimmer(1.0), b, 0.4)
add(riser(1.0, 300, 2000), 23.0, 0.6)

# 24–30: end card
add(impact(1.0), 24.0, 1.0); add(shimmer(4.0), 24.55, 0.9)
add(pad([110, 164.81, 220, 329.63, 493.88], 6.0, 0.13, 1600), 24.0)
for k, f in enumerate([440, 523.25, 659.26, 987.77, 880, 659.26]):
    add(pluck(f, 0.6), 25.0 + k * 0.5, 0.35, 0.5 * np.sin(k))
add(heartbeat(), 28.4, 1.0)

# ---------- master: reverb, glue, limiter ----------
ir_len = int(2.4 * SR); ti = np.arange(ir_len) / SR
def ir(): return rng.standard_normal(ir_len) * np.exp(-ti * 2.6) * (ti > 0.012)
def conv(x, h):
    n = 1 << int(np.ceil(np.log2(len(x) + len(h))))
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[:len(x)]
hl, hr = fft_filter(ir(), lo=200, hi=6000), fft_filter(ir(), lo=200, hi=6000)
wl, wr = conv(L, hl), conv(R, hr)
wl *= 0.25 / (np.abs(wl).max() + 1e-9) * np.abs(L).max(); wr *= 0.25 / (np.abs(wr).max() + 1e-9) * np.abs(R).max()
L2, R2 = L + wl, R + wr
mx = max(np.abs(L2).max(), np.abs(R2).max())
L2, R2 = np.tanh(L2 / mx * 1.6) / np.tanh(1.6), np.tanh(R2 / mx * 1.6) / np.tanh(1.6)
fade = np.ones(N); fs = int(29.0 * SR); fade[fs:] = np.linspace(1, 0, N - fs) ** 2
out = np.stack([L2 * fade, R2 * fade], 1) * 0.89
pcm = (out * 32767).astype('<i2')
with wave.open(sys.argv[1] if len(sys.argv) > 1 else 'halo-audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok')
