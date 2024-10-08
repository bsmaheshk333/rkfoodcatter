from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from .views import fb_views
from .views import api_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("", fb_views.home, name="base"),
    path("search_item/", fb_views.search_menu_item, name="search_item"),
    path('profile/<int:id>/', fb_views.customer_profile, name="profile"),
    path('login/', fb_views.customer_login, name="login"),
    path('register/', fb_views.customer_register, name="register"),
    path("logout/", fb_views.customer_logout, name="logout"),
    path("item_view/<slug:slug>", fb_views.item_detail_view, name="detail_view"),
    path("add_to_cart/<int:id>/", fb_views.add_item_to_cart, name="add_to_cart"),
    path("cart/", fb_views.cart_view, name="cart_view"),
    path("update_cart/<slug:slug>/", fb_views.update_cart, name="update_cart"),
    path("checkout/", fb_views.checkout, name="checkout"),
    path('payment_selection/<int:order_id>/', fb_views.payment_selection, name="payment_selection"),
    path('order_confirmation/<int:order_id>/', fb_views.order_confirmation, name="order_confirmation"),
    path("delivery_status/<int:id>/", fb_views.update_delivery_status, name="delivery_status"),
    # path('profile/order_section/<int:id>/', fb_views.order_section, name="order_section"),
    path('profile/order_section/', fb_views.order_section, name="order_section"),

    # API endpoints
    path('login_api/', api_views.LoginApiView.as_view(), name="login_api"),
    path('register_api/', api_views.RegisterApiView.as_view(), name="register_api"),

    # JWT TOKEN GENERATION endpoint
    path('api/token/', TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('api/token/refresh/', TokenRefreshView.as_view(), name="token_refresh"),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
