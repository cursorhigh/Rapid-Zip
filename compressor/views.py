import os
import io
import random
import string
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render
from .core import compress_image, decompress_file
from .models import CompressionRecord


def random_suffix(length=4):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def dashboard(request):
    records = CompressionRecord.objects.all().order_by('-created_at')
    return render(request, 'dashboard.html', {'records': records})


# ===================== COMPRESSION =====================
@csrf_exempt
def compress_view(request):
    if request.method != 'POST' or 'file' not in request.FILES:
        return JsonResponse({'error': 'file required'}, status=400)

    uploaded = request.FILES['file']
    name, ext = os.path.splitext(uploaded.name)
    safe_name = name.replace(" ", "_")

    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    tmp_name = f"{safe_name}_{random_suffix()}{ext}"
    tmp_path = os.path.join(settings.MEDIA_ROOT, tmp_name)

    # Save uploaded file to media folder
    try:
        with open(tmp_path, 'wb+') as dest:
            for chunk in uploaded.chunks():
                dest.write(chunk)
    except Exception as e:
        return JsonResponse({'error': f'failed to save uploaded file: {str(e)}'}, status=500)

    # Compute hash immediately
    file_hash = CompressionRecord.compute_md5(tmp_path)

    # Check duplicate
    existing = CompressionRecord.objects.filter(file_hash=file_hash).first()
    if existing:
        out_file = existing.output_file or os.path.basename(existing.original_name)
        return JsonResponse({
            'message': 'File already compressed',
            'record_id': existing.id,
            'download_url': f"/api/download/{existing.id}/",
            'out_file': out_file,
            'stats': {
                'original_bytes': existing.original_size,
                'out_bytes': existing.compressed_size,
                'compression_ratio': existing.compression_ratio,
                'quality': existing.quality,
                'down': existing.down,
                'saved': round((1 - existing.compressed_size / existing.original_size) * 100, 2) if existing.original_size > 0 else 0
            }
        })

    # Continue compression
    quality = int(request.POST.get('quality', 50))
    down = int(request.POST.get('down', 2))

    try:
        out_path, stats = compress_image(tmp_path, quality=quality, down=down)
    except Exception as e:
        # keep uploaded file for debugging; return error
        return JsonResponse({'error': f'compression failed: {str(e)}'}, status=500)

    try:
        rec = CompressionRecord.objects.create(
            original_name=uploaded.name,
            file_hash=file_hash,
            quality=quality,
            down=down,
            original_size=stats['original_bytes'],
            compressed_size=stats['out_bytes'],
            payload_size=stats['payload_bytes'],
            base_size=stats['base_bytes'],
            width=stats['w'],
            height=stats['h'],
            output_file=os.path.basename(out_path)
        )
        
        # Calculate saved percentage
        stats['saved'] = round((1 - stats['out_bytes'] / stats['original_bytes']) * 100, 2) if stats['original_bytes'] > 0 else 0
        
    except Exception as e:
        return JsonResponse({'error': f'failed to save record: {str(e)}'}, status=500)

    return JsonResponse({
        'message': 'Compression successful',
        'record_id': rec.id,
        'download_url': f"/api/download/{rec.id}/",
        'out_file': os.path.basename(out_path),
        'stats': stats
    })


# ===================== DECOMPRESSION =====================
@csrf_exempt
def decompress_view(request):
    if request.method != 'POST' or 'file' not in request.FILES:
        return JsonResponse({'error': 'file required'}, status=400)

    uploaded = request.FILES['file']

    # Read bytes and wrap in BytesIO to ensure seekable file-like object
    try:
        uploaded.seek(0)
        raw = uploaded.read()
        fobj = io.BytesIO(raw)
    except Exception as e:
        return JsonResponse({'error': f'failed to read uploaded file: {str(e)}'}, status=500)

    # Perform decompression using core function
    try:
        png_bytes, stats = decompress_file(fobj)
    except Exception as e:
        return JsonResponse({'error': f'decompression failed: {str(e)}'}, status=500)

    # Build decompressed filename
    base_name = os.path.splitext(uploaded.name)[0]
    safe_base = base_name.replace(" ", "_")
    decompressed_name = f"{safe_base}_decompressed_{random_suffix()}.png"

    out_path = os.path.join(settings.MEDIA_ROOT, decompressed_name)
    try:
        with open(out_path, 'wb') as out:
            out.write(png_bytes)
    except Exception as e:
        return JsonResponse({'error': f'failed to save decompressed file: {str(e)}'}, status=500)

    # Return the PNG directly as a downloadable file
    response = HttpResponse(png_bytes, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{decompressed_name}"'
    return response


# ===================== DOWNLOAD ENDPOINT =====================
def download_file(request, record_id):
    """Serve compressed file for download"""
    try:
        record = CompressionRecord.objects.get(id=record_id)
        file_path = os.path.join(settings.MEDIA_ROOT, record.output_file)
        
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'File not found'}, status=404)
        
        response = FileResponse(open(file_path, 'rb'), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{record.output_file}"'
        return response
        
    except CompressionRecord.DoesNotExist:
        return JsonResponse({'error': 'Record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)