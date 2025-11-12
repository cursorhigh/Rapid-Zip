# backend/compressor/core.py
import io
import struct
import zlib
from typing import Tuple, Dict

import numpy as np
from PIL import Image
from scipy.fftpack import dct, idct

# --- Helpers ---------------------------------------------------------------

MAGIC = b"MC2v1"   # math-compress v1

def _dct2(block):
    return dct(dct(block.T, norm='ortho').T, norm='ortho')

def _idct2(block):
    return idct(idct(block.T, norm='ortho').T, norm='ortho')

# standard JPEG-like 8x8 quant matrix (base)
# currently not in use as of its for JPG we dont need for PNG
_Q50 = np.array([
    [16,11,10,16,24,40,51,61],
    [12,12,14,19,26,58,60,55],
    [14,13,16,24,40,57,69,56],
    [14,17,22,29,51,87,80,62],
    [18,22,37,56,68,109,103,77],
    [24,35,55,64,81,104,113,92],
    [49,64,78,87,103,121,120,101],
    [72,92,95,98,112,100,103,99]
], dtype=np.float32)

# zig-zag order (64 indices)
_ZIGZAG_IDX = np.array([
    0, 1, 5, 6,14,15,27,28,
    2, 4, 7,13,16,26,29,42,
    3, 8,12,17,25,30,41,43,
    9,11,18,24,31,40,44,53,
    10,19,23,32,39,45,52,54,
    20,22,33,38,46,51,55,60,
    21,34,37,47,50,56,59,61,
    35,36,48,49,57,58,62,63
    ], dtype=np.int32)

_ZIGZAG_POS = np.argsort(_ZIGZAG_IDX)  # index -> (i,j) position via reshape

def quant_matrix(quality: int) -> np.ndarray:
    q = _Q50.copy()
    # quality scaling (JPEG-like)
    if quality < 50:
        scale = 50.0 / quality
    else:
        scale = 2.0 - (quality / 50.0)
    q = np.clip(np.round(q * scale), 1, 255)
    return q.astype(np.float32)

def _blockify(channel: np.ndarray, block=8):
    H, W = channel.shape
    H2 = ((H + block - 1) // block) * block
    W2 = ((W + block - 1) // block) * block
    padded = np.zeros((H2, W2), dtype=channel.dtype)
    padded[:H, :W] = channel
    # yield block coordinates and block array
    for i in range(0, H2, block):
        for j in range(0, W2, block):
            yield (i, j, padded[i:i+block, j:j+block])

def _unblockify(recon_padded, orig_h, orig_w):
    return recon_padded[:orig_h, :orig_w]

# --- Serialization helpers ------------------------------------------------

def _pack_header(w:int, h:int, channels:int, block_size:int, down:int, quality:int, base_len:int) -> bytes:
    # struct: MAGIC (5 bytes) | width (I) | height (I) | channels (B) | block_size (B) | down (B) | quality (B) | base_len (Q)
    return MAGIC + struct.pack(">II4B Q", w, h, channels, block_size, down, quality, base_len)

def _unpack_header(f) -> Dict:
    magic = f.read(len(MAGIC))
    if magic != MAGIC:
        raise ValueError("Not an MC2v1 file")
    buf = f.read(struct.calcsize(">II4B Q"))
    w, h, channels, block_size, down, quality, base_len = struct.unpack(">II4B Q", buf)
    return {"w": w, "h": h, "channels": channels, "block_size": block_size, "down": down, "quality": quality, "base_len": base_len}

# --- Core compress / decompress -------------------------------------------

def compress_image(path: str, quality: int = 50, down: int = 2) -> Tuple[str, Dict]:
    """
    Compress image at 'path' into path.replace('.png','_mc2.mcmp2').
    Returns (out_path, stats).
    """
    im = Image.open(path).convert("RGB")
    orig_w, orig_h = im.size
    channels = 3

    # 1) Base layer: downsample + save as PNG bytes
    base_w, base_h = orig_w // down, orig_h // down
    base = im.resize((base_w, base_h), resample=Image.LANCZOS)
    buf = io.BytesIO()
    base.save(buf, format="PNG", optimize=True)
    base_bytes = buf.getvalue()
    base_len = len(base_bytes)

    # 2) Upsample base to compute residual
    up_base = base.resize((orig_w, orig_h), resample=Image.BICUBIC)
    orig_arr = np.asarray(im, dtype=np.float32)
    up_arr = np.asarray(up_base, dtype=np.float32)
    residual = orig_arr - up_arr   # can be negative

    # 3) Transform & quantize residual per channel (8x8 DCT)
    Q = quant_matrix(quality)
    block_size = 8

    # We'll store quantized coefficients as int16 arrays per channel, in zigzag order, flattened.
    coef_arrays = []
    H, W = orig_h, orig_w
    for ch in range(3):   # R,G,B channels
        ch_res = residual[:, :, ch]
        flat_coefs = []
        for (i, j, blk) in _blockify(ch_res, block_size):
            if blk.shape != (8,8):
                # pad to 8x8 (shouldn't happen because blockify pads)
                padded = np.zeros((8,8), dtype=blk.dtype)
                padded[:blk.shape[0], :blk.shape[1]] = blk
                blk = padded
            # forward DCT
            d = _dct2(blk)
            q = np.round(d / Q).astype(np.int16)   # quantized coefficients
            # zigzag flatten
            q_flat = q.flatten()[_ZIGZAG_POS]   # shape (64,)
            flat_coefs.append(q_flat)
        coef_arrays.append(np.stack(flat_coefs, axis=0).astype(np.int16))  # (num_blocks, 64)

    # 4) Serialize coefficients: produce a single byte payload using numpy savez (then zlib compress)
    meta = {
        "orig_w": orig_w, "orig_h": orig_h, "down": down, "quality": quality, "block_size": block_size
    }

    # pack: we will create a bytes blob containing arrays in order R,G,B using np.save to buffer
    arr_buf = io.BytesIO()
    # save three arrays with shapes using numpy savez
    np.savez_compressed(arr_buf, r=coef_arrays[0], g=coef_arrays[1], b=coef_arrays[2])
    arr_bytes = arr_buf.getvalue()

    # compress residual bytes with zlib for extra shrinkage
    compressed_payload = zlib.compress(arr_bytes, level=6)

    # 5) create final file: header + base_len + base_bytes + payload
    out_path = path.rsplit(".", 1)[0] + "_mc2.mcmp2"
    with open(out_path, "wb") as fo:
        header = _pack_header(orig_w, orig_h, channels, block_size, down, quality, base_len)
        fo.write(header)
        fo.write(base_bytes)
        # write payload length (8-bytes) then payload
        fo.write(struct.pack(">Q", len(compressed_payload)))
        fo.write(compressed_payload)

    stats = {
        "original_bytes": len(open(path, "rb").read()),
        "base_bytes": base_len,
        "payload_bytes": len(compressed_payload),
        "out_bytes": len(open(out_path, "rb").read()),
        "w": orig_w, "h": orig_h, "down": down, "quality": quality
    }
    return out_path, stats


def decompress_file(fobj) -> Tuple[bytes, Dict]:
    """
    fobj: a file-like object opened in 'rb' (or flask uploaded file).
    Returns (png_bytes, stats) — png_bytes is reconstructed PNG binary bytes.
    """
    # read header
    header = _unpack_header(fobj)
    w = header["w"]; h = header["h"]; channels = header["channels"]
    block_size = header["block_size"]
    down = header["down"]; quality = header["quality"]
    base_len = header["base_len"]

    base_bytes = fobj.read(base_len)
    payload_len_bytes = fobj.read(8)
    (payload_len,) = struct.unpack(">Q", payload_len_bytes)
    payload = fobj.read(payload_len)

    # decompress payload
    arr_bytes = zlib.decompress(payload)
    arr_buf = io.BytesIO(arr_bytes)
    npz = np.load(arr_buf)

    coef_r = npz["r"]  # shape (num_blocks, 64)
    coef_g = npz["g"]
    coef_b = npz["b"]

    # reconstruct per channel blocks
    Q = quant_matrix(quality)
    # compute number of blocks per row/col
    blocks_per_row = ((w + block_size - 1) // block_size)
    blocks_per_col = ((h + block_size - 1) // block_size)

    def rebuild_channel(coef_array):
        # coef_array shape (num_blocks,64)
        recon_padded = np.zeros((blocks_per_col*block_size, blocks_per_row*block_size), dtype=np.float32)
        idx = 0
        for i in range(0, blocks_per_col*block_size, block_size):
            for j in range(0, blocks_per_row*block_size, block_size):
                flat = coef_array[idx]
                idx += 1
                # inverse zigzag
                q = np.zeros(64, dtype=np.float32)
                q[_ZIGZAG_POS] = flat
                q = q.reshape((8,8))
                # dequantize
                d = q * Q
                # inverse DCT
                blk = _idct2(d)
                recon_padded[i:i+8, j:j+8] = blk
        return _unblockify(recon_padded, h, w)

    rec_r = rebuild_channel(coef_r)
    rec_g = rebuild_channel(coef_g)
    rec_b = rebuild_channel(coef_b)

    # load base image and upsample
    base_img = Image.open(io.BytesIO(base_bytes)).convert("RGB")
    up_base = base_img.resize((w, h), resample=Image.BICUBIC)
    up_arr = np.asarray(up_base, dtype=np.float32)

    # reconstructed image = upsampled base + residual (clamp to [0,255])
    recon = up_arr + np.stack([rec_r, rec_g, rec_b], axis=2)
    recon = np.clip(np.round(recon), 0, 255).astype(np.uint8)
    out_img = Image.fromarray(recon, mode="RGB")
    out_buf = io.BytesIO()
    out_img.save(out_buf, format="PNG", optimize=True)
    png_bytes = out_buf.getvalue()

    stats = {"w": w, "h": h, "down": down, "quality": quality, "recon_bytes": len(png_bytes)}
    return png_bytes, stats
