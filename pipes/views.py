import os
import json
import base64
import mimetypes
from email.mime.image import MIMEImage

import pandas as pd

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from .models import Product, ContactMessage, Category, Customer, CompanyImage, Cart, CartItem, QuotationRequest

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
    return render(request, 'pipes/contact.html', context)

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
                    product = Product.objects.get(id=item["id"])

                    # Absolute image URL
                    image_url = None
                    if product.image:
                        try:
                            image_url = request.build_absolute_uri(product.image.url)
                        except Exception:
                            image_url = None

                    products_data.append({
                        "id": product.id,
                        "name": product.name,
                        "part_number": product.part_number or "N/A",
                        "price": float(product.price or 0),
                        "quantity": int(item["quantity"]),
                        "subtotal": float(product.price or 0) * int(item["quantity"]),
                        "image_url": image_url,
                    })

                except Product.DoesNotExist:
                    continue
        
        # Build products HTML with embedded Base64 images
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

                if p["image_url"]:
                    img_html = f"""
                    <img src="{p['image_url']}"
                        width="70"
                        height="70"
                        style="border:1px solid #ddd;
                                border-radius:8px;
                                object-fit:cover;">
                    """
                else:
                    img_html = "No Image"

                products_html += f"""
                <tr>
                    <td style="text-align:center;">{img_html}</td>
                    <td style="text-align:center;">{p['part_number']}</td>
                    <td style="text-align:center;">₹ {p['price']}</td>
                    <td style="text-align:center;">{p['quantity']}</td>
                    <td style="text-align:center;">₹ {p['subtotal']:.2f}</td>
                </tr>
                """
            products_html += """
                </tbody>
            </table>
            """
        else:
            products_html = "<p>No products in cart</p>"
        
        # Build email HTML with info about images
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
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = settings.BREVO_API_KEY

            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )

            sender = {
                "name": "SP Auto Parts Solutions",
                "email": "spautopartssolutions@gmail.com"
            }

            receiver = [
                {
                    "email": "spautopartssolutions@gmail.com",
                    "name": "SP Auto Parts Solutions"
                }
            ]

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                sender=sender,
                to=receiver,
                reply_to={
                    "email": email,
                    "name": name
                },
                subject=f"Quotation Request from {name} - SP Auto Parts",
                html_content=html_content
            )

            api_instance.send_transac_email(send_smtp_email)

            # Clear cart
            cart_id = request.session.get('cart_id')
            if cart_id:
                Cart.objects.filter(id=cart_id).delete()
                if 'cart_id' in request.session:
                    del request.session['cart_id']

            messages.success(request, "Quotation request sent successfully!")

        except ApiException as e:
            print("BREVO ERROR:", e)
            messages.error(request, f"Brevo Error: {e}")

        except Exception as e:
            print("ERROR:", e)
            messages.error(request, f"Error: {e}")
        
        return redirect('cart')
    

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

from django.http import HttpResponse
import socket

def test_email(request):
    try:
        ip = socket.gethostbyname("smtp.gmail.com")
        return HttpResponse(f"Gmail resolves to: {ip}")
    except Exception as e:
        return HttpResponse(f"DNS Error: {e}")
    

from django.contrib.auth.models import User
from django.http import HttpResponse

def create_admin(request):
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            "admin",
            "your@email.com",
            "YourPassword123"
        )
        return HttpResponse("Admin created")

    return HttpResponse("Admin already exists")

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart_id = request.session.get('cart_id')

    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"{product.name} added to cart!")

    return redirect('products')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMessage
from .models import ProductRequest 
def request_product(request):
    
    print("METHOD =", request.method)

    if request.method == "POST":
        print("POST RECEIVED")

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")

        vehicle_company = request.POST.get("vehicle_company")
        vehicle_model = request.POST.get("vehicle_model")
        vehicle_year = request.POST.get("vehicle_year")

        part_name = request.POST.get("part_name")
        part_number = request.POST.get("part_number")

        description = request.POST.get("description")

        image = request.FILES.get("image")

        # Save request in database
        product_request = ProductRequest.objects.create(
            name=name,
            email=email,
            phone=phone,
            vehicle_company=vehicle_company,
            vehicle_model=vehicle_model,
            vehicle_year=vehicle_year,
            part_name=part_name,
            part_number=part_number,
            description=description,
            image=image
        )

        try:

            image_html = ""

            if product_request.image:
                image_url = request.build_absolute_uri(
                    product_request.image.url
                )

                image_html = f"""
                <p><strong>Product Image:</strong></p>

                <img src="{image_url}"
                     width="250"
                     style="border-radius:8px;border:1px solid #ddd;">
                """

            html_content = f"""
            <html>
            <body style="font-family:Arial,sans-serif;">

            <h2 style="color:#2563eb;">
            New Product Request
            </h2>

            <hr>

            <h3>Customer Details</h3>

            <p><strong>Name:</strong> {name}</p>

            <p><strong>Email:</strong> {email}</p>

            <p><strong>Phone:</strong> {phone}</p>

            <hr>

            <h3>Vehicle Details</h3>

            <p><strong>Company:</strong> {vehicle_company}</p>

            <p><strong>Model:</strong> {vehicle_model}</p>

            <p><strong>Year:</strong> {vehicle_year or "N/A"}</p>

            <hr>

            <h3>Requested Product</h3>

            <p><strong>Part Name:</strong> {part_name}</p>

            <p><strong>Part Number:</strong> {part_number or "N/A"}</p>

            <p><strong>Description:</strong></p>

            <p>{description or "No description provided."}</p>

            {image_html}

            </body>
            </html>
            """

            configuration = sib_api_v3_sdk.Configuration()

            configuration.api_key["api-key"] = settings.BREVO_API_KEY

            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )

            sender = {
                "name": "SP Auto Parts Solutions",
                "email": "spautopartssolutions@gmail.com"
            }

            receiver = [
                {
                    "email": "spautopartssolutions@gmail.com",
                    "name": "SP Auto Parts Solutions"
                }
            ]

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                sender=sender,
                to=receiver,
                reply_to={
                    "email": email,
                    "name": name
                },
                subject=f"Product Request - {part_name}",
                html_content=html_content
            )

            api_instance.send_transac_email(send_smtp_email)

            messages.success(
                request,
                "Your product request has been submitted successfully."
            )

        except ApiException as e:

            print(e)

            messages.error(
                request,
                "Request saved, but email could not be sent."
            )

        return redirect("request_product")

    return render(request, "pipes/request_product.html")
