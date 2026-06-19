from django.db import models
from django.contrib.auth.models import User

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.product.price * self.quantity

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):

    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    PRODUCT_TYPES = [
        ('nylon_tubes', 'Nylon Tubes'),
        ('hoses', 'Hoses'),
        ('assemblies', 'Assemblies'),
    ]

    name = models.CharField(max_length=200)
    part_number = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )    
    product_type = models.CharField(max_length=50, choices=PRODUCT_TYPES)
    description = models.TextField()
    specifications = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('product_detail', args=[str(self.id)])
    
    def has_price(self):
        return self.price is not None and self.price > 0
    
    def get_specifications_list(self):
        """Convert specifications text to list for display"""
        if self.specifications:
            return [line.strip() for line in self.specifications.split('\n') if line.strip()]
        return []
    
    def get_image_url(self):
        """Returns image URL or placeholder"""
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return '/static/images/no-image.png'
    
    def image_tag(self):
        """Returns HTML image tag for admin"""
        if self.image and hasattr(self.image, 'url'):
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 8px;" />',
                self.image.url
            )
        return format_html(
            '<div style="width: 100px; height: 100px; background: #f1f5f9; display: flex; align-items: center; justify-content: center; border-radius: 8px;">'
            '<i class="fas fa-box" style="color: #94a3b8;"></i>'
            '</div>'
        )
    image_tag.short_description = 'Image'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save first to get file path
        
        if self.image:
            try:
                # Resize image
                img_path = self.image.path
                img = Image.open(img_path)
                
                # Set max dimensions
                max_size = (800, 800)
                
                if img.height > max_size[0] or img.width > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(img_path, quality=90, optimize=True)
                    
            except Exception as e:
                print(f"Error resizing image: {e}")
    class Meta:
        ordering = ['part_number']


class Customer(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='customers/', null=True, blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def logo_url(self):
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        return None

class CompanyImage(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='company/')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
class QuotationRequest(models.Model):

    name = models.CharField(max_length=100)

    email = models.EmailField()

    phone = models.CharField(max_length=20)

    company = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    message = models.TextField(
        blank=True,
        null=True
    )
    products = models.TextField(blank=True)  # Store products HTML

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class QuotationItem(models.Model):

    quotation = models.ForeignKey(
        QuotationRequest,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.product.name