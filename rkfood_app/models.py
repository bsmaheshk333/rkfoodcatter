import random

from django.db import models
import datetime
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


"""
Documentation
Models defined:
- Restaurant
- Menu
- Menu Items
- Customer
- Booking
- Order
- Payment
- Feedback (survey)

Relationship:
-> 'Restaurant' can have multiple menu, but each Menu associated with one restaurant.
-> 'Menu' can have multiple of Items i.e Menu Items, but each Menu items can be associated
   with only one Menu.
-> Customer can have multiple bookings, but each booking associated with only one Customer
-> Customer can have multiple orders, but each order ties with only one Customer.
-> Orders & payment can be 1-1 relationship. meaning that, there will be only one record
   booking against each payment.
"""


class Restaurant(models.Model):
    name = models.CharField(max_length=100, verbose_name='Restaurant Name')
    address = models.TextField(max_length=500, verbose_name='address')
    phone_number = models.CharField(max_length=12)
    email_addr = models.EmailField()
    opens_at = models.TimeField(null=False, blank=False, verbose_name="opening time")
    close_at = models.TimeField(null=False, blank=False, verbose_name="close time")

    @property
    def formatted_open_time(self):
        opening_time = self.opens_at.strftime("%I:%M:%p")
        return opening_time

    @property
    def formatted_close_time(self):
        return self.close_at.strftime("%I:%M:%p")

    # handle a situation when user(admin) tries to set close time before even its opens time.
    def clean(self):
        if self.close_at <= self.opens_at:
            raise ValidationError("close time must be later than opening time.")


    def __str__(self):
        return f"{self.name} Opens at: {self.formatted_open_time}, Close at: {self.formatted_close_time}"


menu_choice = [
    ('Breakfast', 'Breakfast'),
    ('Lunch', 'Lunch'),
    ('Dinner', 'Dinner'),
    ('beverages', 'beverages')
]

class Menu(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,
                                   related_name='restaurant')
    # breakfast, lunch, dinner
    menu_title = models.CharField(max_length=10, choices=menu_choice, default=menu_choice[0][0])
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.menu_title} for {self.restaurant.name}"


class MenuItems(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='main_menu')
    name = models.CharField(max_length=100)
    image = models.ImageField(default="avatar.jpg", upload_to="menu_items/", verbose_name="image of the food")
    description = models.TextField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Customer(models.Model):
    # one
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="customer_profile")
    phone = models.CharField(max_length=12, unique=True, blank=False, null=False)

    def __str__(self):
        return f"{self.user}"

    # get last login
    @property
    def get_last_login(self):
        print(self.user.last_login)
        return self.user.last_login


ORDER_STATUS = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('canceled', 'Canceled'),
    ('failed', 'failed')
]

PAYMENT_METHODS = [
    ('cash', 'cash'),
    ('credit card', 'credit card'),
    ('online', 'online')
]

DELIVERY_STATUS = [
    ('received', 'received'),
    ('ready', 'ready'),
    ('delivered', 'delivered')
]
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer_ordered")
    menu_item = models.ManyToManyField('MenuItems', through='OrderItem')
    # if in case multiple restaurants
    # restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    # order_qty = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.BooleanField(default=False)  #  todo
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    last_update_date = models.DateTimeField(auto_now=True)
    delivery_status = models.CharField(max_length=15, choices=DELIVERY_STATUS)

    def __str__(self):
        return (f"order{self.id}User:{self.customer.user} || Payment status: {self.payment_status} || Payment Method:{self.payment_method} || "
                f"Order Status: {self.order_status}")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItems, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"order_Id {self.order.id} Qty: {self.quantity} || Unit price: {self.unit_price} || Subtotal: {self.subtotal}"


class UserLoginOtp(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_created=True)

    def save(self, *args, **kwargs):
        if not self.otp:  # if otp is not set then set
            self.otp = str(random.randint(100000, 999999))
        super().save(*args, **kwargs)

    def is_valid(self):
        expire_time = self.created_at + timezone.timedelta(minutes=10)
        return timezone.now() <= expire_time


class CommentModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(MenuItems, on_delete=models.CASCADE)
    comment = models.TextField(max_length=100, verbose_name="comment")
    commented_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.comment


class Cart(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    last_update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"cart belongs to {self.customer}"
    def get_cart_total(self):
        # note -> we are calling cart_items which is a reverse rel to Cart
        # accessing all to CartItem attributes can be done using --> self.cart_items.all())
        # only when your are calling this inside the Cart class
        # suppose if you are trying to access to CartItem through a reverse relationship
        # outside the Cart class (let's say in views.py) you should be using
        # associated variable defined in the CartItem class models.
        # so it should be cart.cart_items.all()
        """
        So, it depends on the context
        where you are accessing this method. If it's inside the Cart model,
        the use of self.cart_items.all() is correct. If it's external
        (like in a view or another model), then cart.cart_items.all() would be
        the right approach.
        """

        return sum(cart_item.item.price * cart_item.quantity for cart_item in self.cart_items.all())

    def get_total_number(self):
        return sum(cart_item.quantity for cart_item in self.cart_items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    item = models.ForeignKey(MenuItems, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cart.customer.username}"

RATING_CHOICES = [
    ('1', 'poor'),
    ('2', 'fair'),
    ('3', 'good'),
    ('4', 'very good'),
    ('5', 'excellent')
]
class Feedback(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    rating = models.CharField(max_length=10, choices=RATING_CHOICES)
    comment = models.TextField(max_length=500)
    posted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"rating: {self.rating} by {self.username}"
