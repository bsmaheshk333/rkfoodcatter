from django.contrib import admin
from .models import (Restaurant, Menu,MenuItems,
                     Customer, Order, CommentModel,
                     UserLoginOtp, CartItem, Cart,
                     OrderItem, Feedback)


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    pass

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    pass

@admin.register(MenuItems)
class MenuItemsAdmin(admin.ModelAdmin):
    pass

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    pass

@admin.register(CommentModel)
class CommentModel(admin.ModelAdmin):
    pass

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    pass

@admin.register(Order)
class OrderModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Cart)
class OrderModelAdmin(admin.ModelAdmin):
    pass

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    pass