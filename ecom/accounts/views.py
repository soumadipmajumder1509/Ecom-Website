from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect,HttpResponse
from .models import Profile
from products.models import *
from accounts.models import Cart, CartItems
from django.contrib.auth.decorators import login_required
import razorpay
from django.conf import settings



def login_page(request):

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = User.objects.filter(username = email)

        if not user_obj.exists():
            messages.warning(request, 'Account not found.')
            return HttpResponseRedirect(request.path_info)


        if not user_obj[0].profile.is_email_verified:
            messages.warning(request, 'Your account is not verified.')
            return HttpResponseRedirect(request.path_info)

        user_obj = authenticate(username = email , password= password)
        if user_obj:
            login(request , user_obj)
            return redirect('/')

        

        messages.warning(request, 'Invalid credentials')
        return HttpResponseRedirect(request.path_info)


    return render(request, 'accounts/login.html' )

def logoutUser(request):
    logout(request)
    return redirect('home')

def register_page(request):

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user_obj = User.objects.filter(username = email)

        if user_obj.exists():
            messages.warning(request, 'Email is already taken.')
            return HttpResponseRedirect(request.path_info)

        user_obj = User.objects.create(first_name = first_name , last_name= last_name , email = email , username = email)
        user_obj.set_password(password)
        user_obj.save()

        messages.success(request, 'An email has been sent on your mail.')
        return HttpResponseRedirect(request.path_info)


    return render(request, 'accounts/register.html')


def activate_email(request, email_token):
    try:
        user = Profile.objects.get(email_token=email_token)
        user.is_email_verified = True
        user.save()
        return redirect('/')
    except Exception as e:
        return HttpResponse('Invalid email token')
    
@login_required(login_url='/login')   
def add_to_cart(request, uid):
    variant = request.GET.get('variant')
    product = Product.objects.get(uid = uid)
    user = request.user
    cart,created = Cart.objects.get_or_create(user = user, is_paid = False)
    cart_item = CartItems.objects.create(cart = cart, product = product)

    if variant:
        variant = request.GET.get('variant')
        size_variant = SizeVariant.objects.get(size_name = variant)
        cart_item.size_Variant = size_variant
        cart_item.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='/login')
def remove_cart(request, cart_item_uid):
    try:
        cart_item = CartItems.objects.get(uid=cart_item_uid)
        cart_item.delete()
    except Exception as e:
        print(e)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='/login')
def cart(request):
    cart_obj = None
    payment = None  # Initialize payment as None at the start
    inr = 0  # Initialize INR to 0 as well

    try:
        # Retrieve the user's unpaid cart
        cart_obj = Cart.objects.get(is_paid=False, user=request.user)
        print(f"Cart ID: {cart_obj.uid}, Items Count: {cart_obj.cart_items.count()}")
        print("Session keys:", request.session.keys())
        print("User is authenticated:", request.user.is_authenticated)

        if request.method == 'POST':
            coupon_code = request.POST.get('coupon')
            coupon_obj = Coupon.objects.filter(coupon_code__icontains=coupon_code).first()
            
            # Validate the coupon
            if not coupon_obj:
                messages.warning(request, 'Invalid Coupon.')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            if cart_obj.coupon:
                messages.warning(request, 'Coupon already exists.')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            if cart_obj.get_cart_total() < coupon_obj.minimum_amount:
                messages.warning(request, f'Amount should be greater than {coupon_obj.minimum_amount}')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            if coupon_obj.is_expired:
                messages.warning(request, 'Coupon Expired.')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            
            # Apply the coupon
            cart_obj.coupon = coupon_obj
            cart_obj.save()
            messages.success(request, 'Coupon applied.')

        # Check if the cart total is greater than 0 before proceeding with payment creation
        if cart_obj.get_cart_total() > 0:
            inr = cart_obj.get_cart_total() * 100
            client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
            payment = client.order.create({
                'amount': inr,
                'currency': 'INR',
                'payment_capture': 1
            })
            cart_obj.razor_pay_order_id = payment['id']
            cart_obj.save()
            print("Payment Details:", payment)
        else:
            messages.info(request, "Your cart is empty.")

    except Cart.DoesNotExist:
        print("No cart found for this user.")
    
    except Exception as e:
        # Log the error for debugging
        print("An error occurred:", str(e))
        messages.error(request, "An unexpected error occurred. Please try again.")

    # Pass context to the template
    context = {
        'cart': cart_obj,
        'payment': payment,
        'inr': inr
    }
    return render(request, 'accounts/cart.html', context)

@login_required(login_url='/login')
def remove_coupon(request, cart_id):
    cart = Cart.objects.get(uid = cart_id)
    cart.coupon = None
    cart.save()
    messages.success(request, 'Coupon Removed.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def success(request):
    order_id = request.GET.get('order_id')
    cart = Cart.objects.get(razor_pay_order_id = order_id)
    cart.is_paid = True
    cart.save()
    return HttpResponseRedirect('Payment Success')



# views.py


# def cart_view(request):
#     cart_item_count = 0
#     cart = None

#     if request.user.is_authenticated:
#         cart = Cart.objects.filter(is_paid=False, user=request.user).first()
#         cart_item_count = cart.cart_items.count() if cart else 0

#     context = {
#         'cart_item_count': cart_item_count,
#         'cart': cart,
#     }
#     return render(request, 'base/base.html', context)
