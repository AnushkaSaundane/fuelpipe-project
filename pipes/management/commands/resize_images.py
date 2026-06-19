from django.core.management.base import BaseCommand
from pipes.models import Product
from PIL import Image
import os

class Command(BaseCommand):
    help = 'Resize all product images'
    
    def add_arguments(self, parser):
        parser.add_argument('--size', type=int, default=800, help='Max size in pixels')
    
    def handle(self, *args, **options):
        max_size = options['size']
        resized_count = 0
        
        for product in Product.objects.all():
            if product.image:
                try:
                    img_path = product.image.path
                    if os.path.exists(img_path):
                        img = Image.open(img_path)
                        
                        # Check if resizing needed
                        if img.height > max_size or img.width > max_size:
                            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                            img.save(img_path, quality=90, optimize=True)
                            resized_count += 1
                            self.stdout.write(f"Resized: {product.name}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error with {product.name}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"Resized {resized_count} images"))