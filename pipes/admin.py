from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ContactMessage, Customer, CompanyImage, Category
from import_export.admin import ImportExportModelAdmin
from .resources import ProductResource

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource

    list_display = ['name', 'product_type', 'price', 'display_image', 'is_featured','category','part_number']
    list_filter = ['product_type', 'is_featured']
    list_display_links = ['name']
    search_fields = ['part_number','name', 'description']
    list_editable = ('is_featured', 'price')
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    import_template_name = 'admin/import_export/import.html'
    fieldsets = (
        ('Basic Information', {
            'fields': ('part_number', 'product_type','category', 'description', 'image')
        }),
        ('Pricing & Features', {
            'fields': ('price', 'is_featured')
        }),
        ('Specifications', {
            'fields': ('specifications',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px; object-fit: cover;" />', obj.image.url)
        return format_html('<div style="width: 50px; height: 50px; background: #f0f0f0; border-radius: 5px; display: flex; align-items: center; justify-content: center; color: #999;"><i class="fas fa-box"></i></div>')
    display_image.short_description = 'Image'
    
    def status_badge(self, obj):
        if obj.is_featured:
            return format_html('<span style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">⭐ Featured</span>')
        return format_html('<span style="background: #6b7280; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">Standard</span>')
    status_badge.short_description = 'Status'

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.image.url)
        return "No Image"
    display_image.short_description = 'Image'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ['name']



@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'is_active']
    list_filter = ['is_active']

@admin.register(CompanyImage)
class CompanyImageAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'created_at']

