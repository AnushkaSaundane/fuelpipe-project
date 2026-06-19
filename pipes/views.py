from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q
from .models import Product, ContactMessage, Category
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, ContactMessage, Customer, CompanyImage
from django.shortcuts import render, redirect
import pandas as pd
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from .models import Cart,CartItem
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from .models import Product, Category, QuotationRequest

def search_price(request):
    query = request.GET.get('q', '')
    product = None
    
    if query:
        # Search by part number or name (case-insensitive)
        products = Product.objects.filter(
            Q(part_number__iexact=query) | 
            Q(name__icontains=query) |
            Q(part_number__icontains=query)
        )
        
        if products.exists():
            product = products.first()
        else:
            messages.info(request, f"No product found with part number or name: '{query}'")
    
    context = {
        'query': query,
        'product': product,
    }
    return render(request, 'pipes/search_price.html', context)

def home(request):
    featured_products = Product.objects.filter(is_featured=True)[:3]
    context = {
        'featured_products': featured_products,
    }
    return render(request, 'pipes/index.html', context)

def about(request):
    return render(request, 'pipes/about.html')

def products(request):

    category_id = request.GET.get('category')
    product_type = request.GET.get('type', '')

    products = Product.objects.all()

    # Filter by category
    if category_id:
        products = products.filter(category_id=category_id)

    # Filter by product type
    if product_type:
        products = products.filter(product_type=product_type)

    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'selected_type': product_type,
        'selected_category': category_id,
    }

    return render(request, 'pipes/products.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(
        product_type=product.product_type
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,

    }
    return render(request, 'pipes/product_detail.html', context)

def customers(request):
    customers_list = [
        {'name': 'Ashok Leyland'},
        {'name': 'Tata Motors'},
        {'name': 'Eicher Motors'},
        {'name': 'Mahindra & Mahindra'},
        {'name': 'JCB'},
    ]
    context = {
        'customers': customers_list,
    }
    return render(request, 'pipes/customers.html', context)

def contact(request):
    product_name = request.GET.get('product', '')

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        
        messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
        return HttpResponseRedirect('/contact/')
    context = {
        'product_name': product_name,
    }
    return render(request, 'pipes/contact.html')

@staff_member_required
def custom_admin_dashboard(request):
    context = {
        'product_count': Product.objects.count(),
        'customer_count': Customer.objects.count(),
        'message_count': ContactMessage.objects.count(),
        'image_count': CompanyImage.objects.count(),
        'recent_messages': ContactMessage.objects.order_by('-created_at')[:5],
        'recent_products': Product.objects.order_by('-created_at')[:3],
    }
    return render(request, 'admin/index.html', context)

@staff_member_required
def upload_products_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_file)
            created_count = 0
            updated_count = 0
            
            for index, row in df.iterrows():
                # Get or create product by part_number
                defaults = {
                    'name': row.get('name', ''),
                    'product_type': row.get('product_type', 'nylon_tubes'),
                    'description': row.get('description', ''),
                    'specifications': row.get('specifications', ''),
                    'price': row.get('price'),
                    'is_featured': bool(row.get('is_featured', False))
                }
                
                # Clean product_type
                product_type = str(defaults['product_type']).lower().replace(' ', '_')
                if product_type not in ['nylon_tubes', 'hoses', 'assemblies']:
                    product_type = 'nylon_tubes'
                defaults['product_type'] = product_type
                
                # Clean price
                if defaults['price']:
                    try:
                        price_str = str(defaults['price']).replace('₹', '').replace('$', '').replace(',', '').strip()
                        defaults['price'] = float(price_str)
                    except:
                        defaults['price'] = None
                
                # Update or create
                part_number = row.get('part_number')
                if part_number:
                    obj, created = Product.objects.update_or_create(
                        part_number=part_number,
                        defaults=defaults
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
            
            messages.success(request, f'Successfully imported {created_count} new products and updated {updated_count} existing products!')
            
        except Exception as e:
            messages.error(request, f'Error importing Excel file: {str(e)}')
        
        return redirect('admin:pipes_product_changelist')
    
    return render(request, 'admin/upload_excel.html')


# ADD TO CART
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def add_to_cart_ajax(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        
        cart_id = request.session.get('cart_id')
        if not cart_id:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
        else:
            try:
                cart = Cart.objects.get(id=cart_id)
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.id
        
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        
        if cart_item:
            cart_item.quantity += 1
            cart_item.save()
        else:
            CartItem.objects.create(cart=cart, product=product, quantity=1)
        
        cart_count = cart.items.count()
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart!',
            'cart_count': cart_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
# CART PAGE
def cart(request):
    cart_id = request.session.get('cart_id')
    cart_items = []
    total = 0

    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
            items = cart.items.select_related('product').all()

            for item in items:
                # Safe price handling
                product_price = item.product.price if item.product.price is not None else 0
                subtotal = product_price * item.quantity
                total += subtotal

                cart_items.append({
                    'product': item.product,
                    'quantity': item.quantity,
                    'subtotal': subtotal
                })
        except Cart.DoesNotExist:
            # Cart doesn't exist, clear the session
            del request.session['cart_id']
        except Exception as e:
            print(f"Cart error: {e}")

    return render(request, 'pipes/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

from django.core.mail import EmailMultiAlternatives
import mimetypes

import os
from django.core.mail import EmailMultiAlternatives
from django.core.files import File
from email.mime.image import MIMEImage

import os
import json
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage

def quotation_request(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        company = request.POST.get("company")
        message = request.POST.get("message")
        product_ids_json = request.POST.get("product_ids")
        
        products_data = []
        if product_ids_json:
            product_items = json.loads(product_ids_json)
            for item in product_items:
                try:
                    product = Product.objects.get(id=item['id'])
                    
                    products_data.append({
                        'id': item['id'],
                        'part_number': product.part_number or 'N/A',
                        'price': product.price or 0,
                        'quantity': item['quantity'],
                        'subtotal': (product.price or 0) * item['quantity'],
                        'image_path': product.image.path if product.image else None,
                        'image_name': os.path.basename(product.image.name) if product.image else None,
                        'image_url': 'http://localhost:8000' + product.image.url
                    })
                except Product.DoesNotExist:
                    pass
        
        # Build products HTML table with CLICKABLE images
        products_html = ""
        if products_data:
            products_html = """
            <table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">
                <thead>
                    <tr style="background: #2563eb; color: white;">
                        <th style="padding: 12px;">Image</th>
                        <th style="padding: 12px;">Part Number</th>
                        <th style="padding: 12px;">Price</th>
                        <th style="padding: 12px;">Quantity</th>
                        <th style="padding: 12px;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
            """
            for p in products_data:
                if p['image_path']:
                    # Clickable image that opens in new tab
                    img_html = f'''
                    <div style="text-align: center;">
                        <a href="{p['image_url']}" target="_blank">
                            <img src="cid:image_{p['id']}" width="70">
                        </a>
                        <br>
                        <a href="{p['image_url']}" target="_blank">
                            🔍 Click to enlarge
                        </a>                    
                        </div>
                    '''
                else:
                    img_html = '<div style="text-align: center;">No Image</div>'
                
                products_html += f"""
                    <tr>
                        <td style="text-align: center; padding: 10px; vertical-align: middle;">{img_html}</td>
                        <td style="text-align: center; padding: 10px;">{p['part_number']}</td>
                        <td style="text-align: center; padding: 10px;">₹ {p['price']}</td>
                        <td style="text-align: center; padding: 10px;">{p['quantity']}</td>
                        <td style="text-align: center; padding: 10px;">₹ {p['subtotal']:.2f}</td>
                    </tr>
                """
            products_html += """
                </tbody>
            </table>
            """
        else:
            products_html = "<p>No products in cart</p>"
        
        # Build email HTML with clickable images
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Quotation Request</title>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .info-box {{ background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: center; border-bottom: 1px solid #ddd; }}
                th {{ background: #1e293b; color: white; }}
                a {{ text-decoration: none; }}
                img {{ transition: transform 0.2s; }}
                img:hover {{ transform: scale(1.05); }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📋 New Quotation Request</h2>
                <p>SP Auto Parts Solution</p>
            </div>
            <div class="content">
                <div class="info-box">
                    <h3>Customer Details:</h3>
                    <p><strong>Name:</strong> {name}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Phone:</strong> {phone}</p>
                    <p><strong>Company:</strong> {company or 'Not provided'}</p>
                    <p><strong>Message:</strong> {message or 'No message'}</p>
                </div>
                
                <h3>🛒 Products Requested:</h3>
                {products_html}
            </div>
        </body>
        </html>
        """
        
        text_content = f"New Quotation Request from {name}\n\nCustomer Details:\nName: {name}\nEmail: {email}\nPhone: {phone}"
        
        try:
            msg = EmailMultiAlternatives(
                subject=f"Quotation Request from {name} - SP Auto Parts",
                body=text_content,
                from_email=settings.EMAIL_HOST_USER,
                to=["spautopartssolutions@gmail.com"]
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Attach images with Content-ID for inline display
            for p in products_data:
                if p['image_path'] and os.path.exists(p['image_path']):
                    try:
                        with open(p['image_path'], 'rb') as f:
                            img_data = f.read()
                            img = MIMEImage(img_data)
                            img.add_header('Content-ID', f'<image_{p["id"]}>')
                            img.add_header('Content-Disposition', 'inline', filename=p['image_name'])
                            msg.attach(img)
                            print(f"Attached image for: {p['part_number']}")              
                    except Exception as e:
                        print(f"Error attaching image for {p['part_number']}: {e}")
            
            msg.send()
            
            # Clear cart
            cart_id = request.session.get('cart_id')
            if cart_id:
                Cart.objects.filter(id=cart_id).delete()
                if 'cart_id' in request.session:
                    del request.session['cart_id']
            
            messages.success(request, 'Quotation request sent successfully!')
            
        except Exception as e:
            print(f"Email error: {e}")
            messages.error(request, f'Error sending request: {str(e)}')
        
        return redirect('cart')
    
    return redirect('cart')

# Add these imports at the top if not already there
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Add these functions to your views.py

def update_cart(request, product_id):
    """Update cart item quantity"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_quantity = int(data.get('quantity', 1))
            
            cart_id = request.session.get('cart_id')
            if cart_id:
                try:
                    cart = Cart.objects.get(id=cart_id)
                    cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
                    if cart_item:
                        if new_quantity > 0:
                            cart_item.quantity = new_quantity
                            cart_item.save()
                        else:
                            cart_item.delete()
                        return JsonResponse({'success': True})
                except Cart.DoesNotExist:
                    pass
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})

def remove_from_cart(request, product_id):
    """Remove item from cart"""
    if request.method == 'POST':
        try:
            cart_id = request.session.get('cart_id')
            if cart_id:
                cart = Cart.objects.get(id=cart_id)
                CartItem.objects.filter(cart=cart, product_id=product_id).delete()
                return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})

from django.http import JsonResponse

def get_cart_count(request):
    cart_id = request.session.get('cart_id')
    count = 0
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
            count = cart.items.count()
        except Cart.DoesNotExist:
            pass
    return JsonResponse({'count': count})