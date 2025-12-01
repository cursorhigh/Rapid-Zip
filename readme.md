# ⚡ Rapid-Zip: Advanced Image Compression System

> **A custom lossy compression algorithm leveraging Discrete Cosine Transform (DCT) and Huffman Coding to achieve 60-80% size reduction with minimal visual quality loss.**


## 🌐 Live Site

**🔗 [Visit RapidZip →](https://rapid-zip.onrender.com/)**
https://rapid-zip.onrender.com/
<div align="center">
  <img src="https://github.com/user-attachments/assets/424ca467-3e9e-45d1-bb2f-b25b19820569" alt="RapidZip Screenshot" width="600"/>
</div>

## 🌐 GitHub Repo
**🔗 [GitHub @ RapidZip →](https://github.com/cursorhigh/Rapid-Zip)**
https://github.com/cursorhigh/Rapid-Zip
## 🎯 Project Overview

Rapid-Zip is a mathematical image compression system that addresses the challenge of storing high-resolution images efficiently. By combining frequency-domain transforms with entropy encoding, we achieve significant file size reduction while maintaining perceptual image quality.

### The Problem
High-resolution PNG images contain substantial redundant information, leading to unnecessarily large file sizes that consume storage and bandwidth. Traditional compression methods either lose too much quality or don't compress enough.

### Our Solution
A hybrid compression pipeline that intelligently removes perceptually redundant data through:
- **Transform-based reduction** using Discrete Cosine Transform (DCT)
<img width="480" height="360" alt="image" src="https://github.com/user-attachments/assets/6e041bd1-03fb-4d4a-9aeb-97f3986824ea" />
- **Entropy-based encoding** using Heap-based Huffman Coding
- **Smart quantization** for controlled quality-to-size tradeoff

---

## 🔬 Technical Architecture

<img width="2848" height="1600" alt="image" src="https://github.com/user-attachments/assets/d4358129-428a-4c63-9dc3-0912ce0cddf0" />

### Compression Pipeline

### Compression Pipeline

```
PNG/JPG Input → RGB to YCbCr → 8×8 Blocks → DCT → Quantization 
→ Zig-Zag Scan → RLE → Huffman Coding → .mcmp2 Output
```

### Decompression Pipeline

```
.mcmp2 Input → Huffman Decode → RLE Decode → Inverse Zig-Zag 
→ Dequantization → Inverse DCT → Block Reassembly → PNG Output
```

---

## 🧮 Mathematical Foundation

### Core Algorithm: 2D Discrete Cosine Transform

The DCT converts spatial image data into frequency coefficients, where high frequencies (fine details) can be discarded with minimal perceptual loss:

$$
F(u,v) = \frac{1}{4} C(u)C(v) \sum_{x=0}^{7}\sum_{y=0}^{7} f(x,y) \cos\left[\frac{(2x+1)u\pi}{16}\right]\cos\left[\frac{(2y+1)v\pi}{16}\right]
$$

Where $C(u) = \frac{1}{\sqrt{2}}$ if $u = 0$, else $1$.

### Key Techniques

| Technique | Purpose | Impact |
|-----------|---------|--------|
| **DCT Transform** | Converts pixels to frequency domain | Enables selective coefficient removal |
| **Quantization** | Reduces coefficient precision | Primary source of compression & loss |
| **Run-Length Encoding** | Compresses sequential zeros | Reduces data volume by 40-60% |
| **Huffman Coding** | Optimal prefix-free encoding | Minimizes final bit representation |

---

## 🏗️ Implementation Details

### Data Structures & Algorithms

**Min-Heap (Priority Queue)**  
Used in Huffman tree construction to build optimal prefix codes with O(n log n) complexity.

**HashMap (Dictionary)**  
Stores symbol-to-frequency mappings for fast lookup during encoding/decoding.

**Static Arrays**  
Zig-zag traversal lookup table for efficient 8×8 block scanning.

### Tech Stack

```
Backend:     Python 3.x, Django, NumPy, SciPy, Pillow
Frontend:    TailwindCSS, Alpine.js
Database:    SQLite3 (compression metadata)
Algorithms:  heapq, collections, custom RLE implementation
Output:      .mcmp2 (custom binary format)
```

---

## 📊 Performance Metrics

### Real-World Test Case

| Metric | Value |
|--------|-------|
| **Input File** | sample1.png (5.84 MB) |
| **Compression Settings** | Quality: 60, Downsample: 2 |
| **Output File** | sample1_mc2.mcmp2 (2.44 MB) |
| **Compression Ratio** | 58.2% size reduction |
| **PSNR** | 32.4 dB (excellent quality) |
| **Processing Time** | ~2.3 seconds |

### Average Performance
- **Size Reduction:** 60-80% depending on image complexity
- **Visual Quality:** Near-identical to original (PSNR > 30 dB)
- **Speed:** Real-time compression for images up to 4K resolution

---

## 🚀 Features

✅ **Dual-Mode Interface** - Separate compression and decompression panels  
✅ **Quality Control** - Adjustable quality (1-100) and downsample (1-8) parameters  
✅ **Duplicate Detection** - MD5 hash checking to avoid reprocessing  
✅ **Visual Feedback** - Real-time progress and compression statistics  
✅ **Batch Ready** - Scalable architecture for multiple file processing  
✅ **Format Preservation** - Maintains image dimensions and color space

---

## 🔧 API Endpoints

**POST** `/api/compress/`  
Accepts PNG/JPG images with optional quality/downsample parameters.  
Returns compressed `.mcmp2` file with statistics.

**POST** `/api/decompress/`  
Accepts `.mcmp2` files.  
Returns reconstructed PNG with original dimensions.

**GET** `/api/download/<record_id>/`  
Serves previously compressed files from database.

---

## 📈 Algorithm Complexity

| Operation | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| DCT per block | O(N²) | O(N²) |
| Huffman tree build | O(n log n) | O(n) |
| Quantization | O(N²) | O(1) |
| RLE encoding | O(n) | O(n) |
| Overall compression | O(WHN²) | O(WH) |

*Where W×H = image dimensions, N = block size (8), n = unique symbols*

---

## 🎓 Research Insights

This project validates the synergy between **mathematical transforms** and **algorithmic data structures**:

1. **Frequency-domain processing** (DCT) naturally separates important from redundant information
2. **Quantization matrices** allow fine-tuned quality-vs-compression tradeoffs
3. **Hybrid approach** (transform + entropy) outperforms single-method compression

The system demonstrates that understanding mathematical foundations enables creation of efficient, practical compression systems competitive with industry standards.

---

## 🔮 Future Enhancements

- [ ] GPU acceleration for DCT computation
- [ ] Adaptive quantization based on image content
- [ ] Multi-threading for parallel block processing
- [ ] Progressive encoding for streaming applications
- [ ] Machine learning-based quantization matrix optimization

---

## 📦 Sample Results

| Original | Compressed | Decompressed |
|----------|------------|--------------|
| 5.84 MB PNG | 2.44 MB .mcmp2 | 5.45 MB PNG |
| Crisp detail | **58% smaller** | Visually identical |

---

## 📝 License

This project is part of academic research in applied mathematics and data structures.

---

**Built with 🧮 Mathematics and 💻 Code**

---

## 👨‍💻 Project Team

**Swadhin** ([@cursorhigh](https://github.com/cursorhigh))  
*Research & Full-Stack Development*

---
