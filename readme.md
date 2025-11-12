## 🧮 **Lossy Image Compression using Mathematics & DSA**

### **1. Problem Statement**

High-resolution PNG images often store redundant information, leading to large file sizes.
This project implements a **custom lossy compression algorithm** that uses **mathematical transforms (DCT)** and **data structures (Heap, HashMap, Arrays)** to reduce size while retaining visual quality.

---

### **2. Objective**

* Develop a **transform + entropy-based** image compression pipeline.
* Apply **Discrete Cosine Transform (DCT)** and **Quantization** to minimize redundancy.
* Implement **Heap-based Huffman Encoding** for entropy compression.
* Measure results using **Compression Ratio** and **PSNR (Peak Signal-to-Noise Ratio)**.

---

### **3. Workflow Overview**

#### 🧩 **Compression Flow**

```
Input Image (.png)
→ RGB → YCbCr Conversion
→ 8×8 Block Division
→ Discrete Cosine Transform (DCT)
→ Quantization (Loss Introduction)
→ Zig-Zag Scan
→ Run-Length Encoding (RLE)
→ Huffman Coding (Heap-based)
→ Output: .mcmp2 (Compressed File)
```

#### 🧩 **Decompression Flow**

```
.mcmp2 File
→ Huffman Decoding
→ RLE Decoding
→ Inverse Zig-Zag
→ Dequantization
→ Inverse DCT
→ Output Image (.png)
```

---

### **4. Mathematical Concepts**

| Concept                             | Description                                                                                                                       |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **DCT (Discrete Cosine Transform)** | Converts spatial pixel data into frequency coefficients. High frequencies represent fine detail (discarded in lossy compression). |
| **Quantization**                    | Reduces precision of frequency coefficients → introduces controlled loss.                                                         |
| **RLE (Run-Length Encoding)**       | Compresses long sequences of zeros from zig-zag ordered blocks.                                                                   |
| **Huffman Coding**                  | Builds optimal prefix codes using a **min-heap**, minimizing bit-length for frequent symbols.                                     |

#### ✳️ Formula (2D DCT)

[
F(u,v) = \frac{1}{4} C(u)C(v) \sum_{x=0}^{7}\sum_{y=0}^{7} f(x,y)
\cos\left[\frac{(2x+1)u\pi}{16}\right]\cos\left[\frac{(2y+1)v\pi}{16}\right]
]
Where
( C(u) = \frac{1}{\sqrt{2}} ) if ( u = 0 ), else 1.

---

### **5. Data Structures Used**

| Component        | Data Structure             | Purpose                        |
| ---------------- | -------------------------- | ------------------------------ |
| Huffman Coding   | **Min-Heap / Binary Tree** | Build optimal codewords        |
| RLE              | **Array**                  | Store and compress zero runs   |
| Zig-Zag Order    | **Static Lookup Table**    | Traverse 8×8 block efficiently |
| Symbol Frequency | **HashMap (dict)**         | Store symbol → frequency pairs |

---

### **6. Algorithmic Summary**

**Compression:**

```pseudo
for each 8x8 block:
    dct = DCT(block)
    q = Quantize(dct)
    zz = ZigZag(q)
    rle = RunLengthEncode(zz)
append all rle blocks
tree = BuildHuffmanTree(rle)
encoded = HuffmanEncode(rle, tree)
save(encoded, tree)
```

**Decompression:**

```pseudo
rle = HuffmanDecode(bitstream, tree)
for each block:
    q = InverseZigZag(rle)
    dct = Dequantize(q)
    block = InverseDCT(dct)
combine blocks → image
```

---

### **7. Tech Stack**

| Layer                   | Tools / Libraries                            |
| ----------------------- | -------------------------------------------- |
| Language                | Python 3.x                                   |
| Framework               | Django                                       |
| Math & Image Processing | NumPy, SciPy, Pillow                         |
| Entropy & DSA           | `heapq`, `collections`, RLE Arrays           |
| Frontend                | TailwindCSS, Alpine.js                       |
| Database                | SQLite3                                      |
| Output Format           | `.mcmp2` custom file (base + zlib residuals) |

---

### **8. Workflow Implementation (Django App)**

| Stage              | Description                                                             |
| ------------------ | ----------------------------------------------------------------------- |
| `/api/compress/`   | Accepts PNG/JPG → compresses using DCT pipeline → returns `.mcmp2` file |
| `/api/decompress/` | Accepts `.mcmp2` → reconstructs and returns decompressed image          |
| Dashboard UI       | Web-based dual-panel interface (Compress / Decompress)                  |
| Database           | Stores compression stats (ratio, size, quality, MD5)                    |

---

### **9. Dry Run Example**

| Step            | Description                                   |
| --------------- | --------------------------------------------- |
| Input           | `sample1.png` (≈ 5.84 MB)                     |
| Params          | Quality = 60, Downsample = 2                  |
| Output File     | `sample1_mc2.mcmp2`                           |
| Compressed Size | 2.44 MB                                       |
| Ratio           | **58.2% space saved**                         |
| PSNR            | ~32.4 dB (good visual quality)                |
| Reconstruction  | `reconstructed.png` (visually near-identical) |

---

### **10. Mathematical Insight**

This compression model is a hybrid of:

* **Transform-based reduction (DCT + Quantization)** — removes perceptually redundant frequencies.
* **Entropy-based encoding (Huffman + RLE)** — optimizes bit-length storage.
* **DSA efficiency** — Heap-based prefix trees + array-based block mapping.

Together, they reduce storage by ~60–80% on average while keeping distortion visually minimal.

---

### **11. Conclusion**

Rapid-Zip demonstrates how **Mathematics (Fourier/DCT transforms)** and **Data Structures (Heap, Arrays, Maps)** can work in unison to solve real-world optimization problems like image compression.
It achieves high compression with minimal loss — validating the power of **applied math + algorithmic efficiency**.

---

### 🧩 Sample Result Visualization

| File                | Size    | Saved           | Visual Quality    |
| ------------------- | ------- | --------------- | ----------------- |
| Original (PNG)      | 5.84 MB | —               | Crisp             |
| Compressed (.mcmp2) | 2.44 MB | **58% smaller** | Nearly identical  |
| Decompressed (PNG)  | 5.45 MB | —               | Slightly smoother |
