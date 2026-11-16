# Image Watermarking using Bit-Plane Slicing

**Course:** Digital Image Processing — Lab Exam, 5th Semester ECI
**Institute:** Indian Institute of Information Technology
**Faculty:** Dr. Tapan Kumar Jain
**Team:** Ayush Agrawal (BT24ECI024) · Ashutosh Porwal (BT24ECI051) · Lakshya Ojha (BT24ECI043) · Prajwal Zagade (BT24ECI013)

---

## 1. What is this project? (in one paragraph)

We hide a secret **text watermark** — `"(c) MY WORK"` — inside a grayscale photo so that nobody can see it. Later we can pull the watermark back out **without needing the original photo**. We do this by replacing one of the image's 8 "bit planes" (usually the least important one) with the watermark. Then we measure how invisible the watermark is and whether it survives attacks like JPEG compression and noise.

**Bottom line:** it is perfectly invisible and perfectly recoverable — but it breaks easily. So it is good for **detecting tampering**, not for protecting copyright.

---

## 2. Key terms you must know

| Term | Meaning |
|---|---|
| **Watermark** | Hidden information (text, logo, ID) inside an image to prove ownership or integrity. |
| **Invisible watermark** | You can't see it by looking at the image. (Ours is invisible.) |
| **Fragile watermark** | Breaks if the image is changed even a little. (Ours is fragile.) Opposite: *robust*. |
| **Blind extraction** | Getting the watermark back without the original image. (Ours is blind.) |
| **Spatial domain** | We edit pixel values directly (not frequency coefficients like DCT/DWT). |
| **Bit plane** | The image made of just one bit position (bit 0, bit 1, … bit 7) of every pixel. |
| **LSB / MSB** | Least Significant Bit (bit 0, weight 1) / Most Significant Bit (bit 7, weight 128). |

---

## 3. The core idea: bit-plane slicing

A grayscale pixel is a number from **0 to 255**, stored as **8 bits**.

```
Pixel value 150  =  1 0 0 1 0 1 1 0   (binary)
Bit position        7 6 5 4 3 2 1 0
Weight            128 64 32 16 8 4 2 1
```

If you take **bit k of every pixel**, you get a black-and-white image called **bit plane k**. So every image splits into 8 planes:

- **Plane 7 (MSB)** → shows the main shapes; looks like the photo.
- **Planes 6–4** → finer edges and details.
- **Planes 3–0** → look like random noise. They barely affect what we see.

👉 **Why this matters:** flipping bit `p` changes the pixel by at most `2^p`.
For the LSB (`p = 0`) that's a change of just **1 out of 255** — completely invisible.
So we can throw away the LSB plane and put our watermark there instead.

---

## 4. How it works (step by step)

### Embedding (hiding the watermark)
1. **Load** the photo and convert it to an 8-bit grayscale matrix `I` (our photo was 1280 × 959).
2. **Make the watermark:** write `"(c) MY WORK"` in white on a black image of the same size, then threshold it so each pixel is `0` or `1`. Call it `W`.
3. **Slice** `I` into its 8 bit planes (and check that putting them back together gives `I` exactly).
4. **Clear bit p** of every pixel using the mask `(255 − 2^p)`, then **OR in** the watermark shifted to position p: `W << p`.
5. **Save** the result `I_w` as **PNG** (lossless — JPEG would destroy the watermark).

### Extraction (getting it back)
1. Take the watermarked image `I_w`.
2. Shift right by `p` and keep only the last bit → that's the recovered watermark `W'`.
3. Compare `W'` with `W` using BER and NC.

### Worked example (p = 0)
```
Original pixel:   150 = 10010110
Watermark bit:    1
Clear LSB:        10010110 AND 11111110 = 10010110
OR in the bit:    10010110 OR  00000001 = 10010111 = 151
```
The pixel changed from 150 → 151. Your eye cannot notice that.

---

## 5. The maths (simple version)

**Bit-plane decomposition** — every pixel is the sum of its bits times their weights:

$$I(x,y)=\sum_{k=0}^{7} b_k(x,y)\,2^k, \qquad b_k(x,y)=\left\lfloor \frac{I(x,y)}{2^k}\right\rfloor \bmod 2$$

**Embedding** — remove the old bit p, add the watermark bit in its place:

$$I_w = I - b_p\,2^p + W\,2^p \qquad\text{(same as } I_w = (I \,\&\, (255-2^p)) \,|\, (W \ll p)\text{)}$$

The error is always small: $|I_w - I| \le 2^p$.

**Extraction:**

$$W' = \left\lfloor \frac{I_w}{2^p} \right\rfloor \bmod 2$$

---

## 6. How we measure success (metrics)

| Metric | What it tells you | Good value |
|---|---|---|
| **MSE** — Mean Squared Error | Average squared difference between original and watermarked image. | Close to 0 |
| **PSNR** — Peak Signal-to-Noise Ratio, `10·log10(255² / MSE)` dB | How invisible the change is. | **> 40 dB** = invisible |
| **SSIM** — Structural Similarity | How similar the images look to a human (structure, contrast, brightness). | Close to 1 |
| **BER** — Bit Error Rate | Fraction of watermark bits recovered wrongly. | 0 |
| **NC** — Normalized Correlation | How well recovered watermark matches the original one. | 1 |

**MSE, PSNR, SSIM** → "Is the watermark invisible?"
**BER, NC** → "Did we get the watermark back correctly?"

---

## 7. Results

### 7.1 Which bit plane should we use?
We embedded the watermark in every plane, one at a time:

| Plane p | MSE | PSNR (dB) | SSIM | BER | NC |
|---|---|---|---|---|---|
| **0 (LSB)** | 0.498 | **51.16** | 0.9980 | 0 | 1 |
| 1 | 2.006 | 45.11 | 0.9925 | 0 | 1 |
| 2 | 7.717 | 39.26 | 0.9744 | 0 | 1 |
| 3 | 32.737 | 32.98 | 0.9274 | 0 | 1 |
| 4 | 121.604 | 27.28 | 0.8397 | 0 | 1 |
| 5 | 580.615 | 20.49 | 0.7225 | 0 | 1 |
| 6 | 2283.986 | 14.54 | 0.6383 | 0 | 1 |
| 7 (MSB) | 9584.517 | 8.32 | 0.5589 | 0 | 1 |

**How to read this:**
- Going up the planes, quality **drops sharply** (PSNR 51 → 8 dB), exactly as the `2^p` rule predicts.
- Planes **0–2** stay invisible (around 40 dB or more). **Plane 0 is the best choice.**
- Recovery is **perfect in every plane** (BER = 0, NC = 1), because PNG is lossless.

### 7.2 Robustness (attacks on the LSB watermark)

| Attack | BER | NC | Result |
|---|---|---|---|
| JPEG compression (quality 90) | 0.391 | 0.126 | Watermark destroyed |
| Random noise (±2 grey levels) | 0.400 | 0.133 | Watermark destroyed |

About **40% of bits go wrong** (50% would be pure guessing), so the text is no longer readable. That shows the watermark is **fragile**.

---

## 8. Implementation details

- **Language / IDE:** Python, Visual Studio Code
- **Libraries:**
  - `OpenCV` — read/write images, draw watermark text, JPEG encoding
  - `NumPy` — bitwise operations (`&`, `|`, `<<`, `>>`)
  - `Matplotlib` — plots and figures
  - `scikit-image` — SSIM
- **Main functions:**

| Function | Job |
|---|---|
| `bit_plane(I, k)` | Returns bit plane k: `(I >> k) & 1` |
| `embed(I, W, p)` | `(I & (255 - 2**p)) | (W << p)` |
| `extract(I_w, p)` | `(I_w >> p) & 1` |
| `psnr(I, I_w)` | PSNR in dB |
| `ber(W, W2)` | Fraction of mismatched bits |
| `nc(W, W2)` | Normalized correlation |

### Minimal core code
```python
import cv2, numpy as np

I = cv2.imread("input.jpg", cv2.IMREAD_GRAYSCALE)          # host image

# Build the binary watermark
W = np.zeros_like(I)
cv2.putText(W, "(c) MY WORK", (50, I.shape[0] // 2),
            cv2.FONT_HERSHEY_SIMPLEX, 4, 255, 10)
W = (W > 127).astype(np.uint8)                              # 0/1

p = 0                                                       # LSB
I_w = (I & (255 - 2**p)) | (W << p)                         # embed
cv2.imwrite("watermarked_p0.png", I_w)                      # MUST be PNG

W2 = (I_w >> p) & 1                                         # extract
mse  = np.mean((I.astype(float) - I_w) ** 2)
psnr = 10 * np.log10(255**2 / mse)
ber  = np.mean(W != W2)
nc   = np.sum(W * W2) / np.sqrt(np.sum(W**2) * np.sum(W2**2))
print(f"PSNR={psnr:.2f} dB  BER={ber:.3f}  NC={nc:.3f}")
```

### Output files
- Figure 1 — original image, its 8 bit planes, and the watermark `W`
- Figure 2 — PSNR and SSIM vs. bit plane
- Figure 3 — original, watermarked (p = 0), amplified difference, extracted watermark
- Figure 4 — watermark extracted after JPEG and after noise
- `watermarked_p0.png` — the final watermarked image

---

## 9. Strengths, limitations, uses

✅ **Strengths**
- Invisible (51.16 dB in LSB)
- Large capacity — 1 bit per pixel, so the watermark can be as big as the image
- Blind extraction; very simple and fast

⚖️ **Trade-off** — a higher plane holds the watermark more strongly but damages quality a lot.

❌ **Limitations**
- Fragile: breaks under JPEG, noise, resizing, cropping
- Grayscale only
- Must be saved as PNG (or another lossless format)
- No secret key — anyone who knows the method can read or remove the watermark

🎯 **Applications** — image authentication, tamper detection, marking medical or forensic images (where *any* change must be detected).

🚀 **Future scope**
- Extend to colour (RGB) images
- Use transform domains (**DCT, DWT, SVD**) for robustness
- Add a secret key (e.g., pseudo-random pixel order)
- Test more attacks (rotation, scaling, cropping, filtering)

---

## 10. Likely viva questions (with short answers)

1. **Why use the LSB?** It changes the pixel by at most 1, so the change is invisible (PSNR > 50 dB).
2. **Why save as PNG, not JPEG?** JPEG is lossy and changes low bits, which destroys the watermark.
3. **What does "blind" mean here?** Extraction needs only `I_w` and `p`, not the original image.
4. **Why does PSNR drop as p increases?** The maximum error is `2^p`, so each higher plane roughly quadruples MSE (about 6 dB loss per plane).
5. **Why is BER ≈ 0.4 after attacks?** Low bits get nearly randomised; 0.5 would be pure guessing.
6. **Fragile vs robust — which is ours and why is that useful?** Fragile. Any edit breaks it, which is exactly what you want for tamper detection.
7. **How could you make it robust?** Embed in transform coefficients (DCT/DWT/SVD) instead of raw pixel bits.
8. **What is the capacity?** M × N bits — one bit per pixel per plane used.
9. **PSNR vs SSIM?** PSNR is pixel error; SSIM measures perceived structural similarity.
10. **Is it secure?** No. Without a key, anyone can read plane 0. Adding a key or encryption would fix this.

---

## 11. References
1. R. C. Gonzalez and R. E. Woods, *Digital Image Processing*, Pearson.
2. I. J. Cox, M. L. Miller, J. A. Bloom, J. Fridrich and T. Kalker, *Digital Watermarking and Steganography*, Morgan Kaufmann.
3. R. G. van Schyndel, A. Z. Tirkel and C. F. Osborne, "A Digital Watermark," *Proc. IEEE ICIP*, 1994.
4. Z. Wang, A. C. Bovik, H. R. Sheikh and E. P. Simoncelli, "Image Quality Assessment: From Error Visibility to Structural Similarity," *IEEE Trans. Image Processing*, 2004.
