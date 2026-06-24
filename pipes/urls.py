from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('products/', views.products, name='products'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('customers/', views.customers, name='customers'),
    path('contact/', views.contact, name='contact'),
    path('search-price/', views.search_price, name='search_price'),
    path('admin/upload-products/', views.upload_products_excel, name='upload_products'),
    path('cart/', views.cart, name='cart'),
    path('quotation-request/',views.quotation_request, name='quotation_request'),
    path('update-cart/<int:product_id>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('add-to-cart-ajax/<int:product_id>/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('get-cart-count/', views.get_cart_count, name='get_cart_count'),
    path('test-email/', views.test_email, name='test_email'),
]