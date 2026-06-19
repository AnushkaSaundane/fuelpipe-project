# add_products.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuelpipe_project.settings')
django.setup()

from pipes.models import Product

# List of products WITHOUT prices
products = [
    {
        'name': 'Nylon Tube 6mm',
        'part_number': 'SP-NT-001',
        'product_type': 'nylon_tubes',
        'description': 'High-quality 6mm nylon tube for automotive fuel lines and air brake systems.',
        'specifications': '• Diameter: 6mm\n• Material: Nylon 11\n• Temperature Range: -40°C to +80°C',
        'price': None,  # No price
        'is_featured': True
    },
    {
        'name': 'Nylon Tube 8mm',
        'part_number': 'SP-NT-002',
        'product_type': 'nylon_tubes',
        'description': '8mm diameter nylon tube for heavy-duty automotive applications.',
        'specifications': '• Diameter: 8mm\n• Material: Nylon 11\n• Pressure Rating: 10 bar',
        'price': None,  # No price
        'is_featured': True
    },
    {
        'name': 'Fuel Hose Assembly',
        'part_number': 'SP-HS-001',
        'product_type': 'hoses',
        'description': 'Complete fuel hose assembly with fittings for easy installation.',
        'specifications': '• Length: 1 meter\n• Includes: Hose, clamps, connectors\n• Material: Synthetic Rubber',
        'price': None,  # No price
        'is_featured': False
    },
    {
        'name': 'Brake Line Assembly Kit',
        'part_number': 'SP-AS-001',
        'product_type': 'assemblies',
        'description': 'Complete brake line assembly for commercial vehicles.',
        'specifications': '• Pre-assembled\n• Pressure tested\n• Brass fittings included',
        'price': None,  # No price
        'is_featured': True
    },
    {
        'name': 'Air Brake Hose',
        'part_number': 'SP-HS-002',
        'product_type': 'hoses',
        'description': 'Durable air brake hose for heavy vehicles.',
        'specifications': '• Working Pressure: 15 bar\n• Temperature: -40°C to +100°C\n• Length: Customizable',
        'price': None,  # No price
        'is_featured': False
    },
    {
        'name': 'Nylon Tube Assembly',
        'part_number': 'SP-AS-002',
        'product_type': 'assemblies',
        'description': 'Complete assembly with nylon tube and fittings.',
        'specifications': '• Tube: 6mm nylon\n• Fittings: Brass\n• Length: As per requirement',
        'price': None,  # No price
        'is_featured': False
    }
]

# Add products to database
for product_data in products:
    # Check if product already exists by name or part_number
    if not Product.objects.filter(name=product_data['name']).exists():
        product = Product.objects.create(**product_data)
        print(f"✅ Added: {product.name}")
    else:
        print(f"⚠️ Already exists: {product_data['name']}")

print(f"\n🎉 Total products in database: {Product.objects.count()}")