from django.urls import path
from . import views
from accounts.views import success,login_page, register_page, activate_email, cart, add_to_cart, remove_cart, remove_coupon

urlpatterns = [
    path('login/', login_page, name="login"), 
    path('logout/', views.logoutUser, name="logout"),  
    path('register/' , register_page , name="register"),
    path('activate/<email_token>/', activate_email, name="activate_email"),
    path('cart/', cart, name="cart"),
    path('add-to-cart/<uid>/', add_to_cart, name="add_to_cart"),
    path('remove-cart/<cart_item_uid>/', remove_cart, name="remove_cart"),
    path('remove-coupon/<cart_id>/', remove_coupon, name="remove_coupon"),
    path('success/', success, name="success")
]
