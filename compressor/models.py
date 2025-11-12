from django.db import models
import hashlib

class CompressionRecord(models.Model):
    # Basic file details
    original_name = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, unique=True , blank=True)  # MD5 (or SHA256 if you prefer)
    output_file = models.CharField(max_length=255, null=True, blank=True) 
    
    # Compression parameters
    quality = models.IntegerField(default=50)
    down = models.IntegerField(default=2)
    
    # Size stats
    original_size = models.IntegerField()
    compressed_size = models.IntegerField()
    payload_size = models.IntegerField()
    base_size = models.IntegerField()
    
    # Derived/computed metrics
    compression_ratio = models.FloatField(help_text="Percentage of size saved", default=0.0)
    
    # Image metadata
    width = models.IntegerField()
    height = models.IntegerField()
    
    # System metadata
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Auto-calculate compression ratio before saving."""
        if self.original_size and self.compressed_size:
            saved = (1 - (self.compressed_size / self.original_size)) * 100
            self.compression_ratio = round(saved, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.original_name} (Q={self.quality}, down={self.down})"

    @staticmethod
    def compute_md5(file_path):
        """Helper to compute MD5 hash for a given file."""
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
