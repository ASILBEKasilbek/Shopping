from django.urls import path
from .views import *

urlpatterns = [
    path('', product_list, name='product_list'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', register, name='register'),
    
    # Savat va buyurtmalar
    path('cart/', cart_view, name='cart'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cart_id>/', remove_from_cart, name='remove_from_cart'),
    path('checkout/', checkout, name='checkout'),
    path('orders/', order_history, name='order_history'),

    # Qidirish
    path('search/', product_search, name='product_search'),  # Alohida qidirish funksiyasi

    # To‘lov
    path('create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('payment-success/', payment_success, name='payment_success'),

    # Sharh qo‘shish
    path('product/<int:product_id>/add-review/', add_review, name='add_review'),

    # Manzillar
    path('addresses/', address_list, name='address_list'),
    path('add-address/', add_address, name='add_address'),
]
