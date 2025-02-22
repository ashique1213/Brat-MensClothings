from django.shortcuts import render,redirect
from . models import Users
from products.models import Brand,Category,ProductDetails,VariantSize
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
import re
from django.http import JsonResponse
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.hashers import check_password
from django.urls import reverse
import random
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import datetime
import time
from offer.models import Brand_Offers,Product_Offers
from django.db.models import Q
from decimal import Decimal
from django.views.decorators.cache import never_cache

from django.contrib.auth import get_user_model
from django.http import HttpResponse

def create_superuser(request):
    User = get_user_model()
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="ashique1213@example.com",
            password="admin@123"
        )
        return HttpResponse("Superuser created successfully!")
    return HttpResponse("Superuser already exists!")



def generate_otp():
    return random.randint(100000, 999999)

@never_cache
def signup_user(request):
    if request.user.is_authenticated:
        return redirect('accounts:home_user')
    
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        phone = request.POST.get('phone').strip()
        email = request.POST.get('email').strip()
        pass1 = request.POST.get('password1').strip()
        pass2 = request.POST.get('password2').strip()

        errors = {}

        if len(username) < 4 or len(username) > 20:
            errors['username_error'] = 'Username must be between 3 and 20 characters long'
        if any(char.isdigit() or char.isspace() for char in username):
            errors['username_error'] = 'Username should not contain numbers or spaces'
        # if Users.objects.filter(username=username).exists():
        #     errors['username_error'] = 'Username already exists'
        if Users.objects.filter(username__icontains=username).exists():
            errors['username_error'] = 'Username already exists'
 
        if phone:  
            phone_pattern = r'^\+?[0-9]{10}$'  
            if not re.match(phone_pattern, phone):
                errors['phone_error'] = 'Phone number must be exactly 10 digits'
            elif Users.objects.filter(phone_number=phone).exists():
                errors['phone_error'] = 'This phone number is already in use.'    

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            errors['email_error'] = 'Invalid email format'
        elif Users.objects.filter(email=email).exists():
            errors['email_error'] = 'Email already exists'

        if pass1 != pass2:
            errors.setdefault('password_error', []).append('Passwords do not match')
        if len(pass1) < 6:
            errors.setdefault('password_error', []).append('Password must be at least 6 characters long')
        if not re.search(r'[A-Z]', pass1):
            errors.setdefault('password_error', []).append('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', pass1):
            errors.setdefault('password_error', []).append('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', pass1):
            errors.setdefault('password_error', []).append('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pass1):
            errors.setdefault('password_error', []).append('Password must contain at least one special character')

        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)
        
        if pass1 == pass2:
            otp = generate_otp()
            otp_expiry = datetime.datetime.now() + datetime.timedelta(seconds=60)

            request.session['otp'] = otp
            request.session['otp_expiry'] = otp_expiry.timestamp()  # Store as timestamp
            request.session['email'] = email
            request.session['username'] = username
            request.session['phone'] = phone
            request.session['password'] = pass1  

            try:
                send_mail(
                    'Your OTP Code',
                    f'Your OTP code is {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                return JsonResponse({'status': 'success', 'redirect_url': reverse('accounts:otp_verify')})
            except Exception as e:
                return JsonResponse({'status': 'error', 'errors': {'email': 'Failed to send OTP. Please try again.'}}, status=500)
        else:
            return JsonResponse({'status': 'error', 'errors': {'password': 'Passwords do not match.'}}, status=400)

    return render(request, 'user/signup.html')


def otp_verify(request):
    if request.user.is_authenticated:
        return redirect('accounts:home_user')
    
    if 'otp' not in request.session or 'otp_expiry' not in request.session:
        # messages.error(request, "You must sign up and request an OTP first!")
        return redirect('signup_user')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        otp_expiry = request.session.get('otp_expiry')

        # Check if OTP matches and not expired
        if entered_otp == str(stored_otp):
            # Check for expiry
            if datetime.datetime.now().timestamp() > otp_expiry:  
                request.session.pop('otp', None)  # Remove expired OTP
                request.session.pop('otp_expiry', None)  # Remove expiry time
                return JsonResponse({'status': 'error', 'errors': {'otp': 'OTP has expired. Please request a new one.'}}, status=400)

            # Create user with hashed password
            user = Users(
                email=request.session['email'],
                username=request.session['username'],
                phone_number=request.session['phone'],
                password=make_password(request.session['password'])  # Hash the password
            )
            user.save()  

            authenticated_user = authenticate(request, username=request.session['username'], password=request.session['password'])
            if authenticated_user is not None:
                login(request, authenticated_user) 
                request.session.flush()  
                return JsonResponse({'status': 'success', 'redirect_url': reverse('accounts:login_user')})

            return JsonResponse({'status': 'error', 'errors': {'authentication': 'User authentication failed. Please try again.'}}, status=400)
        else:
            return JsonResponse({'status': 'error', 'errors': {'otp': 'Invalid OTP.'}}, status=400)

    return render(request, 'user/otp.html')




def resend_otp(request):
    # Initialize resend_otp in session if it doesn't exist
    if 'resend_otp' not in request.session:
        request.session['resend_otp'] = 0  # Set a default value to prevent KeyError
    
    email = request.session.get('email')

    if email:
        otp = generate_otp()
        otp_expiry = datetime.datetime.now() + datetime.timedelta(seconds=60)  # Expire in 60 seconds

        # Update session with new OTP and expiry
        request.session['otp'] = otp
        request.session['otp_expiry'] = otp_expiry.timestamp()

        # Attempt to send the new OTP email
        try:
            send_mail(
                'Your New OTP Code',
                f'Your new OTP code is {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            return JsonResponse({'status': 'success', 'message': 'A new OTP has been sent to your email.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Failed to resend OTP. Please try again.'})
        
    return JsonResponse({'status': 'error', 'message': 'An error occurred. Please try signing up again.'})



@never_cache
def login_user(request):
    if request.user.is_authenticated:
        return redirect('accounts:home_user')

    if request.method == 'POST':
        email = request.POST.get('email').strip()
        password = request.POST.get('password').strip()

        errors = {}
        if not email:
                errors['email'] = 'Email is required.'
        if not password:
                errors['password'] = 'Password is required.'
        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)
        
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            return JsonResponse({'status': 'error', 'errors': {'email': 'Invalid email format.'}}, status=400)

        if len(password) < 6:
            return JsonResponse({'status': 'error', 'errors': {'password': 'Password must be at least 6 characters long.'}}, status=400)

        try:
            user = Users.objects.get(email=email)

            if not user.is_active:
                return JsonResponse({'status': 'error', 'errors': {'account': 'Your account is blocked.'}}, status=403)
            
            authenticated_user = authenticate(request, username=user.username, password=password) 
            if authenticated_user is not None:
                login(request, authenticated_user) 
                redirect_url = reverse('accounts:home_user')
                return JsonResponse({'status': 'success', 'redirect_url': redirect_url}, status=200)
            else:
                return JsonResponse({'status': 'error', 'errors': {'password': 'Invalid password'}}, status=400)

        except Users.DoesNotExist:
            return JsonResponse({'status': 'error', 'errors': {'email': 'User does not exist'}}, status=400)

    return render(request, 'user/login.html')



# def reset_password(request):

#     return render(request,'user/reset_password.html')


@never_cache
def home_user(request):
    products=(
        ProductDetails.objects.select_related('brand')
        .prefetch_related('category','variants')
        .filter(
            Q(is_deleted=False),
            Q(brand__is_deleted=False),
            Q(category__is_deleted=False)
        )

    )
    for product in products:
        product_offer = Product_Offers.objects.filter(
            product_id=product,
            status=True,
            started_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        
        brand_offer = Brand_Offers.objects.filter(
            brand_id=product.brand,
            status=True,
            started_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        
        final_price = product.price
        discount_percentage = 0

        if product_offer and brand_offer:
            if product_offer.offer_price > brand_offer.offer_price:
                final_price = product.price - product_offer.offer_price
                discount_percentage = (product_offer.offer_price / product.price) * Decimal(100)
            else:
                final_price = product.price - brand_offer.offer_price
                discount_percentage = (brand_offer.offer_price / product.price) * Decimal(100)
        elif product_offer:
            final_price = product.price - product_offer.offer_price
            discount_percentage = (product_offer.offer_price / product.price) * Decimal(100)
        elif brand_offer:
            final_price = product.price - brand_offer.offer_price
            discount_percentage = (brand_offer.offer_price / product.price) * Decimal(100)

        product.final_price = final_price
        product.discount_percentage = discount_percentage
    return render(request,'user/home.html',{'products':products})


@never_cache
def logout_user(request):
    request.session.flush()
    logout(request)
    return redirect('accounts:login_user')

def is_staff(user):
    return user.is_staff
   
@never_cache
def admin_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard:admin_dashboard')
    
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            admin = Users.objects.get(email=email)
        except Users.DoesNotExist:
            admin = None
        
        if admin is not None:
            admin = authenticate(request, username=admin.username, password=password)

            if admin is not None and admin.is_superuser:
                login(request, admin)
                return redirect('dashboard:admin_dashboard')
        
        error_message = "Invalid credentials or not a superuser."
        return render(request, 'admin/admin_login.html', {'error_message': error_message})

    return render(request, 'admin/admin_login.html')

@never_cache
def admin_logout(request):
    request.session.flush()
    logout(request)
    return redirect('accounts:admin_login')


@never_cache
def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('accounts:home_user')

    if request.method == 'POST':
        email = request.POST.get('email')
        errors = {}

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            errors['email_error'] = 'Invalid email format'
        elif not Users.objects.filter(email=email).exists():
            errors['email_error'] = 'Email does not exist'

        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        otp = generate_otp()  # Generate OTP

        otp_expiry = datetime.datetime.now() + datetime.timedelta(seconds=60)  # 5 minutes expiry
        request.session['otp'] = otp
        request.session['otp_expiry'] = otp_expiry.timestamp()
        request.session['email'] = email

        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return JsonResponse({'status': 'success', 'redirect_url': reverse('accounts:verify_otp'),'otp_expiry_time': otp_expiry.timestamp()})

    return render(request, 'user/forgot/forgot_password.html')


@never_cache
def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('accounts:home_user')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('otp')  
        otp_expiry = request.session.get('otp_expiry')

        errors = {}

        if not session_otp or not otp_expiry:
            errors['otp_error'] = 'OTP session has expired. Please request a new OTP.'
        elif datetime.datetime.now().timestamp() > otp_expiry:
            errors['otp_error'] = 'OTP has expired. Please request a new one.'
        elif entered_otp != str(session_otp):  
            errors['otp_error'] = 'Invalid OTP entered. Please try again.'
        else:
            return JsonResponse({'status': 'success', 'redirect_url': reverse('accounts:reset_new_password')})

        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)
        
    return render(request, 'user/forgot/reset_otp.html')


def reset_resend_otp(request):
    email = request.session.get('email')  # Retrieve email from session

    if not email:
        return JsonResponse({'status': 'error', 'message': 'Session expired. Please sign up again.'}, status=400)

    if request.method == 'POST':
        new_otp = generate_otp() 
        request.session['otp'] = new_otp
        request.session['otp_expiry'] = (datetime.datetime.now() + datetime.timedelta(minutes=1)).timestamp()

        try:
            send_mail(
                'Your New OTP Code',
                f'Your new OTP code is {new_otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            return JsonResponse({'status': 'success', 'message': 'A new OTP has been sent to your email.'})
    
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Failed to resend OTP. Please try again.'}, status=500)
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
   


@never_cache
def reset_new_password(request):
    if request.user.is_authenticated:
        return redirect('accounts:home_user')

    if request.method == 'POST':
        new_password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')
        
        errors = {}

        if new_password != confirm_password:
            errors['password_error'] = 'Passwords do not match.'
        if len(new_password) < 6:  # You can adjust the password policy as needed
            errors['password_error'] = 'Password must be at least 6 characters long.'
        if not re.search(r'[A-Z]', new_password):
            errors.setdefault('password_error', []).append('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', new_password):
            errors.setdefault('password_error', []).append('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', new_password):
            errors.setdefault('password_error', []).append('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            errors.setdefault('password_error', []).append('Password must contain at least one special character')

        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        # Assuming the user is identified by their email session or another means
        email = request.session.get('email')  # Ensure you set this during OTP generation
        user = Users.objects.get(email=email)
        user.set_password(new_password)  # Use Django's built-in method to hash the password
        user.save()

        del request.session['otp']
        del request.session['otp_expiry']

        return JsonResponse({'status': 'success', 'redirect_url': reverse('accounts:login_user')})

    return render(request, 'user/forgot/reset_forgot_pass.html')


