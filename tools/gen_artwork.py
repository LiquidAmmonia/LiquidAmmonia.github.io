"""Generate zine-poster style artwork for the homepage.

Style rules (from gc-minimal-zine-poster):
aged paper · 70-90% negative space · one small cobalt anchor ·
serif/typewriter microtext · xerox/riso/halftone print defects ·
quiet editorial mood.

Outputs (into assets/img/):
  plate-sun.webp          3:5 paper plate, cobalt disc + orbit dots
  plate-drift.webp        3:5 paper plate, drifting words + small disc
  portrait-halftone.webp  profile photo rendered as a real halftone specimen
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

PAPER = (243, 238, 227)
INK = (38, 35, 25)
COBALT = (37, 65, 224)
MONO = "tools/fonts/IBMPlexMono-Regular.ttf"


def paper(w, h, seed):
    rng = np.random.default_rng(seed)
    base = np.full((h, w, 3), PAPER, dtype=np.float32)
    low = rng.random((h // 24 + 2, w // 24 + 2)).astype(np.float32)
    low = np.asarray(
        Image.fromarray((low * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC),
        dtype=np.float32,
    ) / 255.0
    mottle = (low - 0.5) * 13.0
    grain = rng.normal(0, 3.0, (h, w)).astype(np.float32)
    for c in range(3):
        base[..., c] += mottle + grain
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")


def add_grain(img, sigma=2.4, seed=1):
    rng = np.random.default_rng(seed)
    a = np.asarray(img).astype(np.float32)
    noise = rng.normal(0, sigma, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + noise, 0, 255).astype(np.uint8), img.mode)


def tracked(draw, pos, text, font, fill, tracking=4):
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    return x


def cobalt_disc(size, r, seed):
    """Cobalt disc with riso speckle and a halftone fade toward the bottom."""
    rng = np.random.default_rng(seed)
    disc = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disc)
    dd.ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r], fill=COBALT + (255,))
    a = np.asarray(disc).astype(np.float32)
    speckle = rng.normal(0, 9.0, (size, size))[..., None]
    a[..., :3] = np.clip(a[..., :3] + speckle, 0, 255)
    # halftone fade: punch paper holes that grow toward the bottom
    yy, xx = np.mgrid[0:size, 0:size]
    inside = (xx - size / 2) ** 2 + (yy - size / 2) ** 2 <= r**2
    t = np.clip((yy - (size / 2 - r * 0.1)) / (r * 1.1), 0, 1)
    cell = 11
    phase = ((xx % cell) - cell / 2) ** 2 + ((yy % cell) - cell / 2) ** 2
    hole = phase <= (cell * 0.52 * t) ** 2
    a[..., 3] = np.where(inside & hole & (t > 0.25), 0, a[..., 3])
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def plate_sun():
    random.seed(11)
    W, H = 900, 1500
    im = paper(W, H, seed=3).convert("RGBA")
    cx, cy, r = 452, 585, 195

    d = ImageDraw.Draw(im, "RGBA")
    # misregistered ink ring (the plate shifted on the press)
    d.ellipse([cx - r + 8, cy - r + 6, cx + r + 8, cy + r + 6], outline=INK + (105,), width=3)

    disc = cobalt_disc(W, r, seed=5)
    im.alpha_composite(disc, (0, cy - W // 2))

    d = ImageDraw.Draw(im, "RGBA")
    # sparse orbit of dots
    for _ in range(34):
        ang = random.uniform(0, 2 * math.pi)
        rr = random.uniform(258, 345)
        x, y = cx + rr * math.cos(ang), cy + rr * 1.16 * math.sin(ang)
        col = COBALT + (225,) if random.random() < 0.12 else INK + (random.randint(55, 135),)
        dr = random.uniform(1.1, 2.7)
        d.ellipse([x - dr, y - dr, x + dr, y + dr], fill=col)

    f_l = ImageFont.truetype(MONO, 21)
    f_s = ImageFont.truetype(MONO, 17)
    tracked(d, (66, 72), "PLATE 2 · A STUDY IN COBALT", f_l, INK + (205,), 6)
    tracked(d, (66, H - 112), "YEAN CHENG — NOTES ON INTELLIGENCE", f_s, INK + (150,), 5)
    tracked(d, (W - 150, H - 112), "№ 02", f_s, INK + (150,), 4)

    im = im.filter(ImageFilter.GaussianBlur(0.35))
    im = add_grain(im.convert("RGB"), sigma=2.6, seed=9)
    im.save("assets/img/plate-sun.webp", "WEBP", quality=86, method=6)


def plate_drift():
    random.seed(23)
    W, H = 900, 1500
    im = paper(W, H, seed=8).convert("RGBA")
    cx, cy, r = 615, 420, 92  # small disc, upper-right

    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([cx - r + 6, cy - r + 5, cx + r + 6, cy + r + 5], outline=INK + (100,), width=2)
    im.alpha_composite(cobalt_disc(W, r, seed=6), (cx - W // 2, cy - W // 2))

    # words drifting down-left, fading out
    words = ["agentic", "coding", "visual", "world", "modeling"]
    f = ImageFont.truetype(MONO, 26)
    x, y = 590.0, 560.0
    for i, w in enumerate(words):
        alpha = 170 - i * 26
        d.text((x, y), w, font=f, fill=INK + (max(alpha, 40),))
        x -= 118 + (i % 2) * 30
        y += 128

    f_l = ImageFont.truetype(MONO, 21)
    f_s = ImageFont.truetype(MONO, 17)
    tracked(d, (66, 72), "PLATE 1 · DRIFT", f_l, INK + (205,), 6)
    tracked(d, (66, H - 112), "AFTER A LONG TRAINING RUN", f_s, INK + (150,), 5)
    tracked(d, (W - 150, H - 112), "№ 01", f_s, INK + (150,), 4)

    im = im.filter(ImageFilter.GaussianBlur(0.35))
    im = add_grain(im.convert("RGB"), sigma=2.6, seed=4)
    im.save("assets/img/plate-drift.webp", "WEBP", quality=86, method=6)


def torn_edge_mask(w, h, seed=31):
    """Jittered perimeter polygon as alpha mask — a hand-torn clipping."""
    random.seed(seed)
    pts = []
    steps = 26
    for i in range(steps + 1):  # top, left→right
        pts.append((w * i / steps, random.uniform(0, 7)))
    for i in range(1, steps + 1):  # right
        pts.append((w - random.uniform(0, 7), h * i / steps))
    for i in range(1, steps + 1):  # bottom
        pts.append((w - w * i / steps, h - random.uniform(0, 7)))
    for i in range(1, steps):  # left
        pts.append((random.uniform(0, 7), h - h * i / steps))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(0.6))


def portrait_cobalt():
    """Two-color screenprint portrait: flat paper / cobalt / ink tint bands.

    The source photo is very low-key, so a dot screen collapses into a blob.
    Posterized flat tints — like a layered screenprint — keep the face in
    paper and light cobalt while the dark jacket becomes solid print ink.
    """
    src = Image.open("assets/img/profile.webp").convert("L")
    w0, h0 = src.size
    # crop to head & shoulders so the subject fills the frame
    src = src.crop((int(w0 * 0.14), int(h0 * 0.08), int(w0 * 0.88), int(h0 * 0.86)))
    w, h = src.size
    px = np.asarray(src, dtype=np.float32) / 255.0
    px = np.clip(px**0.45, 0, 1)  # strong lift for the low-key photo
    lo, hi = np.percentile(px, 2), np.percentile(px, 98)
    px = np.clip((px - lo) / (hi - lo), 0, 1)

    # flatten photographic texture into print-like shapes, but keep features
    sm = Image.fromarray((px * 255).astype(np.uint8), "L")
    sm = sm.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.GaussianBlur(0.9))
    a = np.asarray(sm, dtype=np.float32) / 255.0

    # soft-graded bands of ink
    band_ink = np.clip((0.25 - a) / 0.09, 0, 1) * 0.88          # deep shadow → black ink
    band_deep = np.clip((0.52 - a) / 0.10, 0, 1) * np.clip((a - 0.20) / 0.10, 0, 1) * 0.55
    band_light = np.clip((0.76 - a) / 0.10, 0, 1) * np.clip((a - 0.46) / 0.10, 0, 1) * 0.20
    cobalt_amt = np.clip(band_deep + band_light, 0, 1)

    paper_arr = np.array(PAPER, dtype=np.float32)
    cobalt_arr = np.array(COBALT, dtype=np.float32)
    ink_arr = np.array(INK, dtype=np.float32)
    out = paper_arr[None, None, :] * (1 - np.clip(cobalt_amt + band_ink, 0, 1)[..., None])
    out = out + cobalt_arr[None, None, :] * cobalt_amt[..., None]
    out = out + ink_arr[None, None, :] * band_ink[..., None]

    # ink line pass: outline eyes / glasses / jaw so the face reads clearly
    ed = sm.filter(ImageFilter.FIND_EDGES)
    ea = np.asarray(ed, dtype=np.float32) / 255.0
    ea = np.clip((ea - 0.14) / 0.18, 0, 1) ** 1.3 * 0.6
    # keep the line work on the subject, fade it out in the background
    yy, xx = np.mgrid[0:h, 0:w]
    dist2 = ((xx - 0.5 * w) / (0.55 * w)) ** 2 + ((yy - 0.45 * h) / (0.62 * h)) ** 2
    ea = ea * np.clip(1.3 - dist2, 0, 1)
    out = out * (1 - ea[..., None]) + ink_arr[None, None, :] * ea[..., None]

    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")

    img = add_grain(img, sigma=3.2, seed=2).convert("RGBA")
    img.putalpha(torn_edge_mask(w, h))
    img.save("assets/img/portrait-cobalt.webp", "WEBP", quality=88, method=6)


if __name__ == "__main__":
    plate_sun()
    plate_drift()
    portrait_cobalt()
    print("done")
