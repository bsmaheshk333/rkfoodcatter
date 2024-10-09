from django.shortcuts import (render, redirect,
                              get_object_or_404, HttpResponseRedirect,
                              Http404)
from rkfood_app.models import (Restaurant,Menu,
                               MenuItems,
                               Customer,
                               Order, UserLoginOtp, CommentModel, OrderItem, CartItem, Cart)
from django.urls import reverse
from django.db.models import Q
from django.template import TemplateDoesNotExist
from django.contrib.auth import login, logout, authenticate
# from django.contrib.auth.views import login_required, login_not_required ( not supported in django 4.2 version)
from django.contrib.auth.decorators import login_required # use this instead
from django.http import JsonResponse
from django.contrib import messages
from rkfood_app.forms import OTPRequestForm, OTPVerificationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.text import slugify
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.db import transaction, IntegrityError

@login_required(login_url="login/")
def home(request):
    context = {}
    try:
        menu_items = MenuItems.objects.all()
        # initially for a new user cart won't exist, so handling the situation
        cart, created = Cart.objects.get_or_create(customer=request.user)
        if not cart.cart_items.all(): # if cart is empty
            no_of_cart_item = 0  # set count to zero
        else:
            no_of_cart_item = cart.get_total_number()  # else get the total qty in the cart
        context = {
            'menu_items': menu_items,
            'no_of_cart_item': no_of_cart_item
        }
        return render(request, "base.html", context)
    except MenuItems.DoesNotExist:
        return render(request, "error_page.html")
    except TemplateDoesNotExist as ex:
        return render(request, "error_page.html", {'error': ex})

def item_detail_view(request, slug):
    try:
        item = get_object_or_404(MenuItems, slug=slug)
        comments = CommentModel.objects.filter(item=item).order_by('-commented_on')
        existing_comment = CommentModel.objects.filter(user=request.user, item=item).exists()
        if request.method == 'POST':
            comment_text = request.POST.get('comment', None)
            if existing_comment:
                messages.error(request, "You have already commented.")
                return redirect('detail_view', slug=item.slug)

            if comment_text:
                new_comment = CommentModel(user=request.user,item=item, comment=comment_text)
                new_comment.save()
                return redirect('detail_view', slug=item.slug)

            else:
                print('something ===')
        # if method is GET render the details
        return render(request, 'item_detail_view.html',
                      context = {'item': item, 'comments': comments,
                                 'existing_comment': existing_comment})

    except TemplateDoesNotExist as ex:
        context = {'template_error': ex}
        return render(request, "error_page.html", context)



def customer_profile(request, id):
    # TODO implement redis
    try:
        user = User.objects.get(id=id)
        profile = Customer.objects.get(user=user)
        # FIXME
        # ordered_item = OrderItem.objects.all()
        context = {'profile': profile} # 'ordered_item': ordered_item}
        return render(request, 'customer/profile.html',context)
    except Customer.DoesNotExist:
        context = {'profile_error': f"profile does not exist for user '{request.user.username}'"}
        return render(request, "error_page.html", context)
    except TemplateDoesNotExist:
        # do not use JsonResponse render html page instead
        return JsonResponse({'error': 'Template does not exist'}, status=404)


def customer_login(request):
    errors = {}
    # if user is disabled or removed
    if request.user.is_authenticated:
        errors['error'] = 'you must be logged in to access this page'
    if request.method == 'POST':
        username: str = request.POST.get('username', None)
        password: str = request.POST.get('password', None)
        # Validate username and password presence
        if not username:
            errors['username'] = "Invalid username."
        if not password:
            errors['password'] = "Invalid password."
        if not errors:
            # if username and password are provided only then you authenticate
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                with open("user_logged_data.txt", mode="a") as log_file:
                    print(f"{log_file = }")
                    log_file.write(f"user: {request.user}")
                return redirect('/')
            else:
                response = HttpResponse().status_code
                errors['status_code'] = response

        return render(request, "error_page.html",
                      context = {'errors': errors, 'username': username, 'password': password})

    # If GET request, just render the login form
    return render(request, "customer/login.html")

def send_otp_via_email_or_sms(user:User):
    otp_instance = UserLoginOtp.objects.create(user=user)
    otp = otp_instance.otp
    send_mail(
        subject="Your login OTP",
        message=f"your otp is {otp}",
        from_email= settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False
    )
    # send SMS Using Twilio)
    # twilio_client.messages.create(
    #     body=f'Your OTP is {otp}',
    #     from_='<Your Twilio Number>',
    #     to=user.phone_number
    # )

# def customer_login(request):
#     if request.method == 'POST':
#         if 'otp_request' in request.POST:
#             otp_form = OTPRequestForm(request.POST)
#             if otp_form.is_valid():
#                 email_or_phone = otp_form.cleaned_data.get('email_or_phone', None)
#                 user = User.objects.get(email=email_or_phone)
#                 send_otp_via_email_or_sms(user)
#                 request.session['user_id'] = user.id
#                 return redirect('')
#


def customer_register(request):
    if request.method == 'POST':
        username: str = request.POST.get('username', None).strip()
        password: str = request.POST.get('password', None).strip()
        email: str = request.POST.get('email', None).strip()
        phone: str = request.POST.get('phone', None).strip()
        print(f"phone -> {phone = }")
        errors = {}
        # validate email
        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'invalid email address.'
        # validate username
        is_username_exist = User.objects.filter(username=username).exists()
        if is_username_exist:
            errors['username'] = 'user with this name exist'

        if username in ['admin', 'root', 'superuser']:
            errors['username'] = f'the username {username} is restricted.'

        if not any(char.isdigit() for char in password):
            errors['password'] = 'password must contain at least 1 digit.'

        if not phone.isdigit() or len(phone) < 10:
            errors['phone'] = "phone number must be digits and must be at least 10 digits."

        is_phone_no_exist = Customer.objects.filter(phone=phone).exists()
        if is_phone_no_exist:
            errors['phone'] = "Phone number exist already"

        if errors:
            # better to consider render html template to showcase the error
            return JsonResponse(errors, status=400)
        try:
            user, created = User.objects.get_or_create(username=username, email=email)
                                                       #default= {'password': password, 'email':email})
            if created:
                user.set_password(password)
                user.save()
                register_customer_profile = user.customer_profile
                register_customer_profile.phone = phone
                register_customer_profile.save()
            else:
                user.customer_profile.phone = phone
                user.customer_profile.save()
            return redirect("login")
        except:
            errors['db'] = 'database error occurred! Please try again.'
            return JsonResponse(errors, status=400)
    else:
        return render(request, "customer/register.html")

# def customer_register(request):
#     if request.method == 'POST':
#         username = request.POST.get('username', None).strip()
#         password = request.POST.get('password', None).strip()
#         email = request.POST.get('email', None).strip()
#         phone = request.POST.get('phone', None).strip()
#         errors = {}
#         # validate email
#         try:
#             validate_email(email)
#         except ValidationError:
#             errors['email'] = 'invalid email address.'
#         # validate username
#         is_username_exist = User.objects.filter(username=username).exists()
#         if is_username_exist:
#             errors['username'] = 'user with this name exist'
#
#         if username in ['admin', 'root', 'superuser']:
#             errors['username'] = f'the username {username} is restricted.'
#
#         if not any(char.isdigit() for char in password):
#             errors['password'] = 'password must contain at least 1 digit.'
#
#         if not phone or not phone.isdigit() or len(phone) < 10:
#             errors['phone'] = "phone number must be digits and must be at least 10 digits."
#         else:
#             is_phone_no_exist = Customer.objects.filter(phone=phone).exists()
#             if is_phone_no_exist:
#                 errors['phone'] = "Phone number exist already"
#
#         # if any errors
#         if errors:
#             # return render(request, "error_page.html", errors)
#             return JsonResponse({'error': errors}, status=400)
#         # otherwise
#         try:
#             # user, created = User.objects.get_or_create(username=username, email=email)
#             #                                            #default= {'password': password, 'email':email})
#             with transaction.atomic():
#                 # first delete the incomplete customer_profile
#                 incomplete_customer = Customer.objects.filter(user__isnull=True)
#                 if incomplete_customer.exists():
#                     incomplete_customer.delete()
#
#                 user = User.objects.create_user(username=username, password=password, email=email)
#                 Customer.objects.create(user=user, phone=phone)
#                 messages.info(request, "registration success.")
#             return redirect("login")
#         except Exception as e:
#             return JsonResponse({'error': f"{e}"}, status=500)
#             # return render(request, "error_page.ht/ml", errors)
#     else:
#         return render(request, "customer/register.html")


def customer_logout(request):
    try:
        logout(request)
        with open("user_logged_data.txt", mode="a") as log_file:
            print(f"{log_file = }")
        return redirect("base")
    except:
        return render(request, "error_page.html")

def search_menu_item(request):
    # TODO redis
    context = {}
    if request.method == 'POST':
        query_item = request.POST.get('query_item', None)
        # you can have multiple filter depending on requirement
        # if request.method == 'POST':
        if query_item:
            try:
                model_qs = MenuItems.objects.filter(Q(name__icontains=query_item))
                context['menu_items'] = model_qs
                print(f"{query_item = }")
                return render(request, 'search_items.html', context)
            except TemplateDoesNotExist:
                return render(request, "error_page.html")
        else:
            return render(request, "error_page.html")
    else:
        return render(request, "error_page.html")

def add_item_to_cart(request, id):
    try:
        user = request.user
        item = get_object_or_404(MenuItems, id=id)
        # checking if the cart exist for user
        cart, created = Cart.objects.get_or_create(customer=user)
        # now check if the item already in the cart or bag
        # quantity = int(request.POST.get('quantity', 1))
        cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item,
                                    defaults={'quantity': 1,'unit_price': item.price})
        if not created:
            cart_item.quantity += 1
            # not allowed to add more than 5 items in the cart bag
            if cart_item.quantity > 5:
                return render(request, "error_page.html")
            cart_item.save()
        return redirect("cart_view")
    except Cart.DoesNotExist as ex:
        return render(request, "error_page.html", context = {'error': ex})
    except MenuItems.DoesNotExist as ex:
        return render(request, "error_page.html", context = {'error': ex})
    except TemplateDoesNotExist as ex:
        return render(request, "error_page.html", context={'error': ex})


def cart_view(request):
    cart = Cart.objects.get(customer=request.user)
    cart_item = CartItem.objects.filter(cart=cart)
    subtotal_of_all_items = []
    for item in cart_item:
        subtotal_of_all_items.append(item.item.price * item.quantity)
    total_items = []
    for item in cart_item:
        total_items.append(item.quantity)
    context = {
        'cart': cart,
        'cart_item': cart_item,
        'subtotal': sum(subtotal_of_all_items),
        'total_items': sum(total_items)
    }
    return render(request, "cart_view.html", context)


def update_cart(request, slug):
    cart = Cart.objects.get(customer=request.user)
    item = get_object_or_404(MenuItems, slug=slug)
    cart_item = CartItem.objects.get(cart=cart, item=item)
    quantity = request.POST.get('quantity', 1)
    if quantity == "+":
        cart_item.quantity += 1
        cart_item.save()  # save to DB
        messages.success(request, "item added")
    elif quantity == "-":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()  # save to DB
            messages.success(request, "item removed")
    else:
        cart_item.delete()  # else delete the entire item
        messages.success(request, "item removed")
    return redirect("cart_view")


def checkout(request):
    try:
        cart = Cart.objects.get(customer=request.user)
        customer = Customer.objects.get(user=request.user)
        if cart.cart_items.exists():
            # create the order
            order = Order.objects.create(customer= customer,
                                         total_amount = cart.get_cart_total(),
                                         )
            # move cart items to order
            for cart_item in cart.cart_items.all():
                OrderItem.objects.create(order=order, menu_item=cart_item.item,
                                         quantity = cart_item.quantity,
                                         unit_price = cart_item.item.price,
                                         subtotal=cart_item.item.price * cart_item.quantity
                                         )
            cart.cart_items.all().delete()
            return redirect('payment_selection', order_id=order.id)
        # else if cart does not exist
        return redirect('cart_view')
    except Exception as ex:
        return HttpResponse("customer profile does not exist.")
        # return render(request, "error_page.html", {'error': ex})


def payment_selection(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        payment_method: str = request.POST.get('payment_method', None).strip()
        if payment_method:
            order.payment_method = payment_method.lower()
            if payment_method == 'cash':
                order.payment_status = True
                order.delivery_status = "received"
                order.order_status = "completed"
            elif payment_method == ['online',  'credit card']:
                order.payment_status = False
                order.order_status = "canceled"
                # return JsonResponse({'details': 'online mode is not available yet.'}, status=501)
            else:
                order.payment_status = False
                order.order_status = "pending"
        order.save()
        return redirect('order_confirmation', order_id=order.id)

    return render(request, 'payment_selection.html', {'order': order})


def order_confirmation(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        context = {'order': order}
        return render(request, 'order_confirmation.html', context)
    except Order.DoesNotExist as ex:
        return render(request, "error_page.html", context={'error': ex})


# only admin or owner can modify the delivery status
# def update_delivery_status(request):
#     # orders = Order.objects.all()
#     ordered_items = OrderItem.objects.all()
#     ordered_items = OrderItem.objects.select_related('order').all()
#     if request.method == 'POST':
#         delivery_status = request.POST.get('delivery_status')
#         if delivery_status in dict(DELIVERY_STATUS):
#             ordered_items.order.delivery_status = delivery_status
#             ordered_items.save()  # save to DB
#             return redirect("update_delivery_status")
#     return render(request, 'customer_ordered_delivery_status.html', context={'ordered_items': ordered_items})

def update_delivery_status(request):
    ordered_items = OrderItem.objects.select_related('order').all()  # Fetch related orders efficiently
    # get the DELIVERY_STATUS from model
    DELIVERY_STATUS = Order._meta.get_field('delivery_status').choices
    if request.method == 'POST':
        delivery_status = request.POST.get('delivery_status')
        order_id = request.POST.get('order_id')  # Including the order id from input to know which order to update
        if delivery_status in dict(DELIVERY_STATUS):  # Validate if the status is in the choices
            order = Order.objects.get(id=order_id)
            order.delivery_status = delivery_status  # Update the delivery status
            order.save()  # Save to the DB
            return redirect("update_delivery_status")
    return render(request, 'customer_ordered_delivery_status.html',
                  context={'ordered_items': ordered_items, 'DELIVERY_STATUS': DELIVERY_STATUS})


def order_section(request):
    customer = Customer.objects.get(user=request.user)
    order = Order.objects.filter(customer=customer)
    if order.exists():
        ordered_item = OrderItem.objects.filter(order__in=order)
        context = {
            'ordered_item': ordered_item,
        }
        return render(request, 'customer/ordered_item.html', context)
    else:
        return JsonResponse({'error': 'no orders found'}, status=404)

def generate_receipt(request):
    pass




















