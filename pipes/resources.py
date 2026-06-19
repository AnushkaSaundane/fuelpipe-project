from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Product

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        #import_id_fields = ['part_number']  # Use part_number as unique identifier
        fields = ('part_number', 'name', 'product_type', 'description', 
                 'specifications', 'price', 'is_featured')
        skip_unchanged = True
        report_skipped = False
        
    # Add any custom validation if needed
    def before_import_row(self, row, **kwargs):
        # Convert product_type to lowercase if needed
        if 'product_type' in row:
            row['product_type'] = row['product_type'].lower().replace(' ', '_')
    
    # Convert price to decimal
    def before_save_instance(self, instance, using_transactions, dry_run):
        if hasattr(instance, 'price'):
            try:
                # Remove any currency symbols and convert to decimal
                price_str = str(instance.price).replace('₹', '').replace('$', '').replace(',', '').strip()
                instance.price = float(price_str)
            except (ValueError, TypeError):
                instance.price = None