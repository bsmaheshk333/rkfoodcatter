import itertools

from django.shortcuts import (render, redirect,get_object_or_404)
from rkfood_app.models import (Restaurant,Menu,MenuItems,
                               Customer,Order, UserLoginOtp,
                               CommentModel, OrderItem, CartItem,
                               Cart, Feedback)
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
    try:
        context = {}
        no_of_cart_item = 0
        user = request.user.id
        cart, created = Cart.objects.get_or_create(customer=user)
        if cart.cart_items.exists():  # if cart is not empty
            no_of_cart_item = cart.get_total_number()  # get the total qty in the cart
            context['no_of_cart_item'] = no_of_cart_item
            print(f"{no_of_cart_item = }")
        context['no_of_cart_item'] = no_of_cart_item
        return render(request, "base.html", context)
    except TemplateDoesNotExist:
        return JsonResponse({'error': 'page not found'}, status=404)


@login_required(login_url="login/")
def show_menu_items(request):
    get_restaurant = request.POST.get('restaurant', None)
    try:
        # selected_restaurant = Restaurant.objects.get(name=get_restaurant)
        # # menu__restaurant -- Menu has a foreign key to Restaurant, so we can filter this way
        # menu_items = MenuItems.objects.filter(menu__restaurant=selected_restaurant)
        menu_items = MenuItems.objects.all()
        context = {'menu_items': menu_items}
        return render(request, "menu_items.html", context)

    except MenuItems.DoesNotExist:
        return render(request, "menu_items.html",
                      {'error': "Restaurant not found",})


@login_required(login_url="login/")
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
        # handle GET
        item = get_object_or_404(MenuItems, slug=slug)
        comment = CommentModel.objects.filter(item=item)
        comment_count = comment.count()
        return render(request, 'item_detail_view.html',
                      context = {'item': item, 'comments': comments,'existing_comment': existing_comment,
                                 'comment_count': comment_count})

    except TemplateDoesNotExist as ex:
        context = {'template_error': ex}
        return render(request, "error_page.html", context)


@login_required(login_url="login/")
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
    username = request.POST.get('username') if request.method == 'POST' else ''
    password = request.POST.get('password') if request.method == 'POST' else ''

    if request.user.is_authenticated:
        return redirect('menu_item')

    if request.method == 'POST':
        if not username:
            errors['username'] = "Invalid username."
        if not password:
            errors['password'] = "Invalid password."

        if username and password and not errors:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                with open("user_logged_data.txt", mode="a") as log_file:
                    log_file.write(f"user: {request.user}\n")
                return redirect('menu_item')
            else:
                errors['invalid_credentials'] = "Invalid username or password."

    return render(request, "customer/login.html", {
        'errors': errors,
        'username': username,
        'password': password,
    })


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


def customer_register(request):
    if request.method == 'POST':
        username = request.POST.get('username', None).strip()
        password = request.POST.get('password', None).strip()
        email = request.POST.get('email', None).strip()
        phone = request.POST.get('phone', None).strip()
        errors = {}
        if not username.islower():
            errors['error'] = 'please enter username in lowercase format.'
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Invalid email address.'

        # Validate username
        is_username_exist = User.objects.filter(username=username).exists()
        if is_username_exist:
            errors['username'] = 'User with this name already exists.'

        if username in ['admin', 'root', 'superuser']:
            errors['username'] = f'The username {username} is restricted.'

        # Validate password
        if not any(char.isdigit() for char in password):
            errors['password'] = 'Password must contain at least 1 digit.'

        # Validate phone number
        if not phone.isdigit() or len(phone) < 10:
            errors['phone'] = "Phone number must be digits and at least 10 digits."

        is_phone_no_exist = Customer.objects.filter(phone=phone).exists()
        if is_phone_no_exist:
            errors['phone'] = "Phone number already exists."

        if errors:
            return JsonResponse(errors, status=400)
        try:
            with transaction.atomic():
                # Create the user (not saved yet)
                user, created = User.objects.get_or_create(username=username, email=email)
                if created:
                    user.set_password(password)
                    user.save()
                    # Create or update the customer profile
                    register_customer_profile = user.customer_profile
                    register_customer_profile.phone = phone
                    register_customer_profile.save()
                send_mail(
                    subject="Thanks for registering with RKFoodCatter",
                    message='Thank you for registering with us! Your account has been created. '
                            'Regards, RKFoodCatter. Happy Eating...',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                )
            return redirect("login")
        except:
            # if created delete it
            if created:
                user.delete()
            errors['email'] = 'Failed to send confirmation email. Please try again.'
            return JsonResponse(errors, status=500)
    else:
        return render(request, "customer/register.html")


@login_required(login_url="login/")
def customer_logout(request):
    try:
        logout(request)
        with open("user_logged_data.txt", mode="a") as log_file:
            print(f"{log_file = }")
        return redirect("login")
    except:
        return render(request, "error_page.html")


@login_required(login_url="login/")
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


@login_required(login_url="login/")
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


@login_required(login_url="login/")
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


@login_required(login_url="login/")
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


@login_required(login_url="login/")
def checkout(request):
    try:
        cart = Cart.objects.get(customer=request.user)
        customer = Customer.objects.get(user=request.user)
        if cart.cart_items.exists():
            # create the order if cart is not empty
            order = Order.objects.create(customer= customer,
                                         total_amount = cart.get_cart_total(),
                                         payment_status=False, order_status="pending")
            # move cart items to order section
            for cart_item in cart.cart_items.all():
                OrderItem.objects.create(order=order, menu_item=cart_item.item,
                                         quantity = cart_item.quantity,
                                         unit_price = cart_item.item.price,
                                         subtotal=cart_item.item.price * cart_item.quantity
                                         )
            cart.cart_items.all().delete()
            return redirect('payment_selection', order_id=order.id)
        else:
            return redirect('cart_view')
    except Exception as ex:
        return HttpResponse(f"{ex}")
        # return render(request, "error_page.html", {'error': ex})


@login_required(login_url="login/")
def payment_selection(request, order_id):
    user = request.user
    order = get_object_or_404(Order, id=order_id)
    order_item = OrderItem.objects.filter(order=order)
    if request.method == 'POST':
        payment_method: str = request.POST.get('payment_method', None).strip()
        if payment_method:
            order.payment_method = payment_method.lower()
            if payment_method == 'cash' and order.payment_status is False:
                order.payment_status = True
                order.delivery_status = "placed"
                order.order_status = "completed"
                # order.save()
                send_mail(
                    subject="Your payment is successful",
                    message=f'Payment Mode: {payment_method}'
                            f"\nOrder status: {order.order_status}"
                            '\nRegards, RKFoodCatter. \nHappy Eating...',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                )
            elif payment_method == ['online',  'credit card']:
                # temporarily setting it to false due to unavailability
                order.payment_status = False
                order.order_status = "Canceled"
                # return JsonResponse({'details': 'online mode is not available yet.'}, status=501)
            else:
                order.payment_status = False
                order.delivery_status = "Transaction failed"
                order.order_status = "Failed"
                order.delete()
            # send_mail(
            #     subject="Your payment is successful",
            #     message=f'Payment Mode: {payment_method}'
            #             f"\nOrder status: {order.order_status}"
            #             '\nRegards, RKFoodCatter. \nHappy Eating...',
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[user.email],
            # )
            # FIXME currently not saving the order other than cash
            order.save()
            return redirect('order_confirmation', order_id=order.id)

    return render(request, 'payment_selection.html', {'order': order})


@login_required(login_url="login/")
def order_confirmation(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        context = {'order': order}
        return render(request, 'order/order_confirmation.html', context)
    except Order.DoesNotExist as ex:
        return render(request, "error_page.html", context={'error': ex})


@login_required(login_url="login/")
def manage_delivery_status(request):
    user = request.user
    selected_status = request.GET.get('status', 'all')
    DELIVERY_STATUS = Order._meta.get_field('delivery_status').choices
    if selected_status == 'all':
        ordered_items = OrderItem.objects.select_related('order').all()
    else:
        ordered_items = OrderItem.objects.select_related('order').filter(order__delivery_status=selected_status)
    if request.method == 'POST':
        delivery_status = request.POST.get('delivery_status')
        order_id = request.POST.get('order_id')
        if delivery_status in dict(DELIVERY_STATUS):
            order = Order.objects.get(id=order_id)
            order.delivery_status = delivery_status
            send_mail(
                subject="Update on Your Order Status",
                message=f'Your current order Status: {order.delivery_status}\n'
                        f'Regards, RKFoodCatter. \nHappy Eating...',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
            order.save()
            return redirect("update_delivery_status")

    return render(request, 'manage_delivery_status.html', {
        'ordered_items': ordered_items,
        'DELIVERY_STATUS': DELIVERY_STATUS,
    })


@login_required(login_url="login/")
def customer_orders(request):
    user = request.user
    selected_status = request.GET.get('status')
    print(request.GET, "status")
    print(f"{selected_status = }")
    context = dict()
    error = {}
    # try:
    customer = Customer.objects.get(user=user)
    if selected_status == 'all':
        all_orders = Order.objects.filter(customer=customer)
        print(f"{all_orders = }")
        context['orders'] = all_orders
    if selected_status == 'recent':
        recent_order = Order.objects.filter(customer=customer,
                                            payment_status=True,).order_by('-last_update_date').first()
        recent_order_item = OrderItem.objects.filter(order=recent_order)
        context['orders'] = recent_order_item
    if selected_status == 'past':
        past_orders = Order.objects.filter(customer=customer, payment_status=True)
        if past_orders.exists():
            past_order = OrderItem.objects.filter(order__in=past_orders)
            context['orders'] = past_order
        else:
            error['order_history'] = "there are not orders"
    if selected_status == 'failed':
        failed_orders = Order.objects.filter(customer=customer, payment_status=False)
        if failed_orders.exists():
            pending_ordered_item = OrderItem.objects.filter(order__in=failed_orders)
            context['orders'] = pending_ordered_item
        else:
            error['pending_orders'] = "there are not failed orders"
    ORDER_STATUS = Order._meta.get_field('order_status').choices
    context['ORDER_STATUS'] = ORDER_STATUS

    return render(request, "order/orders.html", context)
    # except:
    #     return JsonResponse(error, status=500)


@login_required(login_url="login/")
def customer_feedback(request):
    error = {}
    rating: str = request.POST.get('rating').lower().strip()
    message: str = request.POST.get('message').lower().strip()
    # user = User.objects.get(username=request.user)
    user = request.user
    if request.method == 'POST':
        try:
            feedback, created = Feedback.objects.get_or_create(username=user,
                                                               email=user.email,
                                                               rating=rating,
                                                               comment=message)
            with transaction.atomic():
                if created:
                    feedback.save()
                    # send user a confirmation mail
                    send_mail(
                        subject="Thanks for your feedback",
                        message=''
                                'Regards, RKFoodCatter. Happy Eating...',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                    )
            return render(request, "feedback_confirmation.html")
        except Exception as ex:
            if created:
               feedback.delete()
            error['feedback_error'] = ex
            return render(request, "error_page.html", context=error)
    else:
        return render(request, "base.html")


@login_required(login_url="login/")
def view_feedback(request):
    try:
        feedback = Feedback.objects.all().order_by("-posted_on")
        feedback_count = feedback.count()
        context = {
            'feedbacks': feedback,
            'feedback_count':feedback_count
        }
        return render(request, "feedback_confirmation.html", context)
    except Feedback.DoesNotExist as e:
        return render(request, "error_page.html", context={'error': e})
