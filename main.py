"""
Image Watermarking using Bit-Plane Slicing  (VS Code ready)
============================================================
HOW TO RUN IN VS CODE
  1. Put this file (main.py) and your image (input.jpeg) in the same folder.
  2. Open the folder in VS Code.
  3. Terminal ->  pip install -r requirements.txt
  4. Press the "Run Python File" (play) button, or run:  python main.py
  Results are saved in the folder "results" and also shown in pop-up windows.

MATHEMATICAL MODEL
  Bit planes   : I(x,y) = sum_{k=0..7} b_k(x,y) * 2^k
                 b_k(x,y) = floor(I(x,y) / 2^k) mod 2
  Embedding    : I_w = I - b_p*2^p + W*2^p  =  (I AND (255-2^p)) OR (W << p)
  Extraction   : W' = floor(I_w / 2^p) mod 2          (blind, no original needed)
  MSE          : 1/(MN) * sum (I - I_w)^2
  PSNR         : 10*log10(255^2 / MSE)  [dB]
  BER          : 1/(MN) * sum [W != W']
  NC           : sum(W*W') / sqrt(sum(W^2) * sum(W'^2))
"""

import os
import numpy as np
import cv2
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim

# ======================= SETTINGS (change these) =======================
HERE = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(HERE, "input.jpeg")   # your host image
OUT_DIR = os.path.join(HERE, "results")         # output folder
WATERMARK_TEXT = "(c) MY WORK"                  # text hidden in the image
EMBED_PLANES = (0, 2)                           # bit planes to embed in (0 = LSB)
SHOW_PLOTS = True                               # False = only save, no pop-ups
# =======================================================================


# ------------------------------ core maths ------------------------------
def bit_plane(img, k):
    """b_k(x,y) = floor(I / 2^k) mod 2"""
    return (img >> k) & 1


def slice_all(img):
    return [bit_plane(img, k) for k in range(8)]


def reconstruct(planes):
    """I = sum b_k * 2^k"""
    return sum((planes[k].astype(np.uint16) << k) for k in range(8)).astype(np.uint8)


def embed(img, wm, p):
    """I_w = (I & (255 - 2^p)) | (W << p)"""
    return ((img & (255 - (1 << p))) | (wm.astype(np.uint8) << p)).astype(np.uint8)


def extract(img_w, p):
    return bit_plane(img_w, p)


def mse(a, b):
    return np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)


def psnr(a, b):
    m = mse(a, b)
    return float("inf") if m == 0 else 10 * np.log10(255.0 ** 2 / m)


def ber(w, w2):
    return np.mean(w != w2)


def nc(w, w2):
    w, w2 = w.astype(float), w2.astype(float)
    d = np.sqrt((w ** 2).sum() * (w2 ** 2).sum())
    return (w * w2).sum() / d if d else 0.0


def make_watermark(shape, text):
    """Binary text watermark W in {0,1}, same size as the host image."""
    h, w = shape
    canvas = np.zeros((h, w), np.uint8)
    scale = w / 600.0
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, scale * 1.6, 3)
    cv2.putText(canvas, text, ((w - tw) // 2, (h + th) // 2),
                cv2.FONT_HERSHEY_DUPLEX, scale * 1.6, 255,
                max(2, int(3 * scale)), cv2.LINE_AA)
    return (canvas > 127).astype(np.uint8)


def finish(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, name), dpi=110)


# --------------------------------- main ---------------------------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # STEP 1: load image -> grayscale matrix I
    color = cv2.imread(IMAGE_PATH)
    if color is None:
        raise SystemExit(f"Cannot read image: {IMAGE_PATH}\n"
                         "Put your image next to main.py and name it input.jpeg")
    I = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    print(f"[1] Image loaded, size = {I.shape[1]} x {I.shape[0]}")

    # STEP 2: create binary watermark W
    W = make_watermark(I.shape, WATERMARK_TEXT)
    print(f"[2] Watermark created: '{WATERMARK_TEXT}'")

    # STEP 3: bit-plane slicing
    planes = slice_all(I)
    assert np.array_equal(reconstruct(planes), I)
    print("[3] Bit-plane slicing done (reconstruction is lossless)")
    fig, ax = plt.subplots(2, 5, figsize=(18, 7))
    ax = ax.ravel()
    ax[0].imshow(I, cmap="gray"); ax[0].set_title("Original (gray)")
    for k in range(8):
        n = 7 - k
        ax[k + 1].imshow(planes[n] * 255, cmap="gray")
        ax[k + 1].set_title(f"Bit plane {n}" + (" (MSB)" if n == 7 else " (LSB)" if n == 0 else ""))
    ax[9].imshow(W * 255, cmap="gray"); ax[9].set_title("Binary watermark W")
    for a in ax: a.axis("off")
    finish(fig, "1_bit_plane_slices.png")

    # STEP 4 + 5: embed in every plane and measure quality
    print("\n[4-5] Embed in each plane and measure quality")
    print(f"{'Plane':>5} {'MSE':>10} {'PSNR(dB)':>9} {'SSIM':>7} {'BER':>6} {'NC':>6}")
    rows = []
    for p in range(8):
        Iw = embed(I, W, p)
        Wx = extract(Iw, p)
        r = (p, mse(I, Iw), psnr(I, Iw), ssim(I, Iw, data_range=255), ber(W, Wx), nc(W, Wx))
        rows.append(r)
        print(f"{r[0]:>5} {r[1]:>10.3f} {r[2]:>9.2f} {r[3]:>7.4f} {r[4]:>6.3f} {r[5]:>6.3f}")
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ps = [r[0] for r in rows]
    ax[0].plot(ps, [r[2] for r in rows], "o-"); ax[0].set_title("PSNR vs embedding plane")
    ax[0].set_xlabel("Bit plane p"); ax[0].set_ylabel("PSNR (dB)"); ax[0].grid(alpha=.3)
    ax[1].plot(ps, [r[3] for r in rows], "s-r"); ax[1].set_title("SSIM vs embedding plane")
    ax[1].set_xlabel("Bit plane p"); ax[1].set_ylabel("SSIM"); ax[1].grid(alpha=.3)
    finish(fig, "2_psnr_ssim_vs_plane.png")

    # STEP 6: embed + extract for chosen planes
    print("\n[6] Embedding and extraction for chosen planes")
    for p in EMBED_PLANES:
        Iw = embed(I, W, p)
        Wx = extract(Iw, p)
        cv2.imwrite(os.path.join(OUT_DIR, f"watermarked_p{p}.png"), Iw)  # PNG keeps bits
        cv2.imwrite(os.path.join(OUT_DIR, f"extracted_watermark_p{p}.png"), Wx * 255)
        print(f"    plane {p}: PSNR={psnr(I, Iw):.2f} dB, BER={ber(W, Wx):.3f}, NC={nc(W, Wx):.3f}")
        fig, ax = plt.subplots(1, 4, figsize=(18, 4.8))
        ax[0].imshow(I, cmap="gray"); ax[0].set_title("Original I")
        ax[1].imshow(Iw, cmap="gray"); ax[1].set_title(f"Watermarked I_w (p={p})\nPSNR={psnr(I, Iw):.2f} dB")
        diff = np.abs(I.astype(int) - Iw.astype(int)) * (255 // max(1, 1 << p))
        ax[2].imshow(diff, cmap="gray"); ax[2].set_title("Difference (amplified)")
        ax[3].imshow(Wx * 255, cmap="gray"); ax[3].set_title(f"Extracted W'  BER={ber(W, Wx):.3f}  NC={nc(W, Wx):.3f}")
        for a in ax: a.axis("off")
        finish(fig, f"3_embed_extract_p{p}.png")

    # STEP 7: robustness (attacks)
    print("\n[7] Robustness test on LSB watermark (fragile by design)")
    Iw = embed(I, W, 0)
    _, enc = cv2.imencode(".jpg", Iw, [cv2.IMWRITE_JPEG_QUALITY, 90])
    Ij = cv2.imdecode(enc, cv2.IMREAD_GRAYSCALE)
    noisy = np.clip(Iw.astype(int) + np.random.RandomState(0).randint(-2, 3, Iw.shape), 0, 255).astype(np.uint8)
    for name, img in (("JPEG q=90", Ij), ("Noise +-2", noisy)):
        Wx = extract(img, 0)
        print(f"    {name}: BER={ber(W, Wx):.3f}  NC={nc(W, Wx):.3f}")
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.8))
    ax[0].imshow(extract(Ij, 0) * 255, cmap="gray"); ax[0].set_title("Extracted after JPEG q=90")
    ax[1].imshow(extract(noisy, 0) * 255, cmap="gray"); ax[1].set_title("Extracted after noise +-2")
    for a in ax: a.axis("off")
    finish(fig, "4_robustness.png")

    print(f"\nDone. All results saved in: {OUT_DIR}")
    if SHOW_PLOTS:
        plt.show()


if __name__ == "__main__":
    main()
