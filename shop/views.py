from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.conf import settings
from django.http import JsonResponse
import stripe

from .models import Product, Cart, Order, OrderItem, Address, Review

# Stripe sozlamalari
stripe.api_key = settings.STRIPE_SECRET_KEY


### AUTHORIZATION VIEWS ###
def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("product_list")
        else:
            return render(request, "login.html", {"error": "Noto‘g‘ri login yoki parol"})
    return render(request, "login.html")

def user_logout(request):
    logout(request)
    return redirect("login")

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})


### PRODUCT VIEWS ###
def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})

def product_search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query)) if query else Product.objects.all()
    return render(request, 'product_list.html', {'products': products, 'query': query})


### CART VIEWS ###
@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    for item in cart_items:
        item.total_price = item.product.price * item.quantity  # Har bir mahsulot uchun umumiy narx
    total_price = sum(item.total_price for item in cart_items)  # Jami narx

    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.delete()
    return redirect('cart')


### CHECKOUT & PAYMENT VIEWS ###
@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return redirect('cart')

    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Manzil tekshirish
    address = Address.objects.filter(user=request.user).first()
    if not address:
        return redirect('add_address')

    return render(request, 'checkout.html', {'cart_items': cart_items, 'total_price': total_price, 'address': address})

@login_required
def create_checkout_session(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return JsonResponse({'error': 'Savatchangiz bo‘sh'}, status=400)

    total_price = sum(item.product.price * item.quantity for item in cart_items)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(item.product.price * 100),
                    'product_data': {
                        'name': item.product.name,
                    },
                },
                'quantity': item.quantity,
            }
            for item in cart_items
        ],
        mode='payment',
        success_url='http://127.0.0.1:8000/payment-success/',
        cancel_url='http://127.0.0.1:8000/checkout/',
    )

    return JsonResponse({'sessionId': session.id})

@login_required
def payment_success(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    order = Order.objects.create(user=request.user, total_price=total_price)
    for item in cart_items:
        OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)

    cart_items.delete()

    return render(request, 'payment_success.html')


### ORDER HISTORY ###
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})


### ADDRESS VIEWS ###
@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'address_list.html', {'addresses': addresses})

@login_required
def add_address(request):
    if request.method == 'POST':
        full_name = request.POST['full_name']
        phone = request.POST['phone']
        city = request.POST['city']
        street = request.POST['street']
        postal_code = request.POST['postal_code']

        Address.objects.create(user=request.user, full_name=full_name, phone=phone, city=city, street=street, postal_code=postal_code)
        return redirect('address_list')

    return render(request, 'add_address.html')


### REVIEW VIEWS ###
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 1))
        comment = request.POST.get('comment', '')

        Review.objects.create(product=product, user=request.user, rating=rating, comment=comment)
    
    return redirect('product_detail', pk=product.id)

