from PIL import Image
import os
from django.core.files import File
from io import BytesIO

def resize_image(image_field, max_size=(800, 800)):
    """Resize image to specified dimensions while maintaining aspect ratio"""
    if not image_field:
        return
    
    # Open the image
    img = Image.open(image_field.path)
    
    # Check if resizing is needed
    if img.height <= max_size[0] and img.width <= max_size[1]:
        return
    
    # Calculate new dimensions
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save the resized image
    img.save(image_field.path, quality=90, optimize=True)
    
    return True

def optimize_image(image_field):
    """Optimize image for web"""
    if not image_field:
        return
    
    img = Image.open(image_field.path)
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'LA', 'P'):
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = rgb_img
    
    # Save with optimization
    img.save(image_field.path, 'JPEG', quality=85, optimize=True)