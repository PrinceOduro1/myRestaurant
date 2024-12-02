from django.shortcuts import render,redirect,get_object_or_404
from .models import FASTMENU,FASTUSER,CartItem,Order,Payment
from django.contrib import messages
from django.conf import settings
import re
import stripe
from django.contrib.auth.models import User,auth
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import cache_control
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt

def index(request):
    first_name = None
    if request.user.is_authenticated:
        try:
            # Get the corresponding FASTUSER object based on the user's email
            fastuser = FASTUSER.objects.get(email=request.user.username)
            fullname = fastuser.fullname
            # Split the fullname and take the first part (the first name)
            first_name = fullname.split()[0] if fullname else None
            print(f"User first name found: {first_name}")  # Debug print to check the first name
        except FASTUSER.DoesNotExist:
            print(f"No FASTUSER found for email: {request.user.email}")  # Debug print for missing FASTUSER
            first_name = request.user.username  # Fallback to username if FASTUSER doesn't exist

    context = {
        'is_authenticated': request.user.is_authenticated,
        'username': first_name,  # Pass first name to template
    }
    return render(request, 'index.html', context)



def signup(request):
    if request.method == "POST":
        fullname = request.POST['fullname']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        # Validate password strength
        if len(password) >= 8 and re.search(r'[A-Z]', password) and re.search(r'[!@#$%^&*()_+={}\[\]:;"\'<>,.?/-]', password):
            if password == confirm_password:
                # Check if the user already exists
                if FASTUSER.objects.filter(email=email).exists():
                    messages.error(request, 'Email is already registered.')
                    return redirect('signup')

                # Create Django User object
                user = User.objects.create_user(username=email, password=password)

                # Create corresponding FASTUSER entry
                fastuser = FASTUSER(fullname=fullname, email=email, password=make_password(password))
                fastuser.save()

                messages.success(request, 'Account created successfully. Please log in.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
                return redirect('signup')
        else:
            messages.error(request, 'Password must be at least 8 characters long, include an uppercase letter, and a special character.')
            return redirect('signup')

    return render(request, 'signup.html')

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(username=email,password=password)
        print(user)

        if user is not None:
            auth.login(request,user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('index')

    return render(request,'login.html')

def admin_dashboard(request):
    if request.method == 'POST':
        foodname = request.POST['foodname']
        food_category = request.POST['food_category']
        price = float(request.POST['price'])
        elapse_time = request.POST['elapse_time']
        meal_picture = request.FILES['meal_picture']
        print(food_category)

        food_menu = FASTMENU(foodname=foodname,food_category=food_category,price=price,elapse_time=elapse_time,meal_picture=meal_picture)
        food_menu.save()
        messages.success(request,'Menu added successfully')
        return redirect('admin_dashboard')

    return render(request,'admin_dashboard.html')

def logout(request):
    auth.logout(request)
    return redirect('index')

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def menu(request):
    # Fetch all the menu items from the database
    menu_items = FASTMENU.objects.all()

    # Group the menu items by category
    grouped_menu = {
        'BREAKFAST': menu_items.filter(food_category='BREAKFAST'),
        'LUNCH': menu_items.filter(food_category='LUNCH'),
        'SUPPER': menu_items.filter(food_category='SUPPER'),
        'DRINKS': menu_items.filter(food_category='DRINKS'),
        'PASTRIES': menu_items.filter(food_category='PASTRIES'),
    }

    # Pass the grouped menu items to the template
    return render(request, 'menu.html', {'grouped_menu': grouped_menu})

import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@login_required
def add_to_cart(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            food_item_id = data.get('food_item_id')
            quantity = data.get('quantity', 1)
            logger.info(f"Received data: food_item_id={food_item_id}, quantity={quantity}")

            # Get the food item and user
            food_item = FASTMENU.objects.get(id=food_item_id)
            user = request.user  # Django's default User instance
            try:
                # Find the corresponding Users instance
                user = FASTUSER.objects.get(email=user.username)
            except FASTUSER.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found in custom Users table.'}, status=404)

            # Check if the item is already in the user's cart
            cart_item, created = CartItem.objects.get_or_create(
                user=user, food_item=food_item,
                defaults={'quantity': quantity}
            )

            if not created:
                # If the item already exists in the cart, update the quantity
                cart_item.quantity += quantity
                cart_item.save()

            # Return a success response
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Error adding item to cart: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
    return render(request,'cart.html')

@login_required
def view_cart(request):
    try:
        # Get the logged-in user
        user = request.user
        try:
            # Find the corresponding Users instance
            user = FASTUSER.objects.get(email=user.username)
        except FASTUSER.DoesNotExist:
            return HttpResponse("User not found in custom Users table.", status=404)

        # Get all cart items for the user
        cart_items = CartItem.objects.filter(user=user)
        
        # Calculate the total price (optional)
        total_price = sum(item.food_item.price * item.quantity for item in cart_items)

        # Pass cart items and total price to the template
        context = {
            'cart_items': cart_items,
            'total_price': total_price,
        }
        return render(request, 'cart.html', context)
    except Exception as e:
        logger.error(f"Error retrieving cart: {str(e)}")
        return HttpResponse("An error occurred while retrieving the cart.", status=500)
    
def delete_cart(request, cart_id):
    try:
        # Get the cart item by its id
        cart_item = get_object_or_404(CartItem, id=cart_id)
        cart_item.delete()  # Delete the cart item
        messages.success(request, "Cart item deleted successfully")
    except:
        messages.error(request, "Failed to delete cart item")
    
    # Redirect back to the cart view
    return redirect('view_cart')

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_order(request):
    # Step 1: Retrieve user's cart items
    # Get the logged-in user
    user = request.user
    try:
        # Find the corresponding Users instance
        user = FASTUSER.objects.get(email=user.username)
    except FASTUSER.DoesNotExist:
        return HttpResponse("User not found in custom Users table.", status=404)
    

    cart_items = CartItem.objects.filter(user=user)
    
    if not cart_items.exists():
        messages.error(request, "Your cart is empty. Please add items to your cart.")
        return redirect('view_cart')

    # Step 2: Calculate total price and save the order
    total_price = sum(item.food_item.price * item.quantity for item in cart_items)
    
    # Create a new order and associate the cart items with it
    order = Order.objects.create(
        user=user,
        total_amount=total_price,
        status="Pending"  # Default status is 'Pending'
    )

    # Add cart items to the order using the ManyToMany relationship
    order.items.set(cart_items)  # Associate all cart items with the order

    # Step 3: Clear the user's cart after order is placed
    cart_items.delete()  # Clear the cart after the order is saved

    # Step 4: Redirect to the order confirmation page
    context = {
        'order': order
    }
    return render(request, 'order_confirmation.html', context)

@csrf_exempt
def create_payment(request):
    order_id = request.GET.get("order_id")  # Get the order_id from the request
    if not order_id:
        return HttpResponse("No order ID provided.", status=400)

    try:
        # Retrieve the order based on the order_id
        order = Order.objects.get(id=order_id)

        # Create a Stripe PaymentIntent
        amount = int(order.total_amount * 100)  # Convert the amount to cents

        # Create a PaymentIntent with Stripe
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",  # You can change the currency as needed
            metadata={"order_id": order.id},
        )

        # Save the PaymentIntent's ID in your database (optional)
        payment = Payment.objects.create(
            order=order,
            stripe_payment_intent=intent.id,
            amount=order.total_amount,
            status="Pending",
        )

        # In create_payment view, update the redirect URL to match the new path
        # In create_payment view
        return redirect(f'/payment-form/{order.id}/')  # Corrected URL with hyphen
        # Now the URL includes the order_id in the path


    except Order.DoesNotExist:
        return HttpResponse("Order not found.", status=404)
    
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    endpoint_secret = "your-webhook-secret"

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)

        if event["type"] == "payment_intent.succeeded":
            intent = event["data"]["object"]
            payment = Payment.objects.get(stripe_payment_intent=intent["id"])
            payment.status = "Completed"
            payment.save()

        return JsonResponse({"status": "success"})
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({"error": "Invalid signature"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
from django.shortcuts import render, redirect
from .models import FASTUSER, Order

def payment_success(request):
    # Get the logged-in user
    user = request.user
    try:
        # Find the corresponding Users instance
        user = FASTUSER.objects.get(email=user.username)
    except FASTUSER.DoesNotExist:
        return HttpResponse("User not found in custom Users table.", status=404)
    
    # Get all orders for the user
    orders = Order.objects.filter(user=user, status='Pending')  # Filter pending orders

    # Update the status of each order to 'Approved'
    for order in orders:
        order.status = 'Approved'
        order.save()  # Save the changes to the database

    # Optionally, pass any data to the template
    return render(request, 'payment_success.html', {'user': user})


def del_model(request):

    orders = Order.objects.all()
    orders.delete()

    return redirect('index')
@login_required
def payment_form(request, order_id):
    try:
        # Retrieve the order based on the order_id
        order = Order.objects.get(id=order_id)

        # Retrieve the associated payment for this order
        payment = Payment.objects.get(order=order)

        # Ensure the payment has a valid stripe_payment_intent (which is an ID)
        if not payment.stripe_payment_intent:
            return HttpResponse("PaymentIntent not found for this order.", status=400)

        # Retrieve the PaymentIntent from Stripe using the stored ID
        intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent)

        # Now access the client_secret from the PaymentIntent object
        client_secret = intent.client_secret

        # Pass the order and client_secret to the template
        context = {
            'order': order,
            'client_secret': client_secret,
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,  # Your Stripe public key
        }

        return render(request, 'payment.html', context)

    except Order.DoesNotExist:
        return HttpResponse("Order not found.", status=404)
    except Payment.DoesNotExist:
        return HttpResponse("Payment not found for this order.", status=404)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)

def don(request):
    pass