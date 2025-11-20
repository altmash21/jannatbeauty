"""
Clean Accounts Views - Separated Customer and Seller Logic
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.core.exceptions import FieldError
from django.utils import timezone
from django.http import JsonResponse
from functools import wraps
import json

from .models import Profile, SellerProfile, PasswordResetOTP, RegistrationOTP
from .forms import CustomerRegistrationForm, SellerRegistrationForm, ProfileUpdateForm, SellerProfileUpdateForm
from orders.models import Order, OrderItem


# AJAX: Check if email is already taken
from django.views.decorators.http import require_GET

@require_GET
def check_email_taken(request):
    email = request.GET.get('email', '').strip()
    exists = False
    if email:
        from django.contrib.auth.models import User
        exists = User.objects.filter(email=email).exists()
    return JsonResponse({'taken': exists})


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

def register_choice(request):
    """Let users choose between customer or seller registration"""
    return render(request, 'accounts/register_choice.html')


def register_customer(request):
    """Customer registration - send OTP to email"""
    if request.user.is_authenticated:
        return redirect('accounts:customer_dashboard')
    
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            # Store registration data in session
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            request.session['registration_email'] = email
            request.session['registration_password'] = password
            
            # Generate OTP
            otp_instance = RegistrationOTP.generate_otp(email, password)
            
            # Print OTP to console for debugging (local development only)
            if settings.DEBUG:
                print(f"\n{'='*70}")
                print(f"{' '*20}REGISTRATION OTP GENERATED")
                print(f"{'='*70}")
                print(f"Email: {email}")
                print(f"{'='*70}")
                print(f"{' '*25}OTP CODE: {otp_instance.otp_code}")
                print(f"{'='*70}")
                print(f"Expires at: {otp_instance.expires_at}")
                print(f"{'='*70}\n")
            
            # Send email
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@jannatbeauty.com')
            send_mail(
                subject='Verify Your Email - Jannat Beauty',
                message=f'''Hello,\n\nYour verification code is: {otp_instance.otp_code}\n\nThis code will expire in 10 minutes.\n\nBest regards,\nJannat Beauty Team''',
                from_email=from_email,
                recipient_list=[email],
                fail_silently=False,
            )
            
            messages.success(request, f'OTP has been sent to {email}. Please check your inbox or console.')
            return redirect('accounts:verify_registration_otp')
    else:
        form = CustomerRegistrationForm()
    
    return render(request, 'accounts/register_customer.html', {'form': form})


# ============================================================================
# RESEND OTP VIEWS
# ============================================================================

def resend_registration_otp(request):
    """Resend registration OTP to email (AJAX)"""
    email = request.session.get('registration_email')
    if not email:
        return JsonResponse({'success': False, 'message': 'Session expired. Please start registration again.'})
    try:
        # Get password from latest unused OTP (if exists)
        latest_otp = RegistrationOTP.objects.filter(email=email, is_used=False).order_by('-created_at').first()
        password = latest_otp.password if latest_otp else None
        if not password:
            return JsonResponse({'success': False, 'message': 'No password found for this registration.'})
        # Generate new OTP
        otp_instance = RegistrationOTP.generate_otp(email, password)
        # Print OTP to console for debugging (local development only)
        if settings.DEBUG:
            print(f"\n{'='*70}")
            print(f"{' '*20}RESEND REGISTRATION OTP")
            print(f"{'='*70}")
            print(f"Email: {email}")
            print(f"{'='*70}")
            print(f"{' '*25}OTP CODE: {otp_instance.otp_code}")
            print(f"{'='*70}")
            print(f"Expires at: {otp_instance.expires_at}")
            print(f"{'='*70}\n")
        # Send email
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@jannatbeauty.com')
        send_mail(
            subject='Verify Your Email - Jannat Beauty',
            message=f'''Hello,\n\nYour new verification code is: {otp_instance.otp_code}\n\nThis code will expire in 10 minutes.\n\nBest regards,\nJannat Beauty Team''',
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        return JsonResponse({'success': True, 'message': f'New OTP sent to {email}.'})
    except Exception as e:
        import traceback
        if settings.DEBUG:
            print(f"\n{'='*60}")
            print(f"ERROR RESENDING REGISTRATION OTP:")
            print(f"Error: {str(e)}")
            traceback.print_exc()
            print(f"{'='*60}\n")
        return JsonResponse({'success': False, 'message': f'Failed to resend OTP: {str(e)}'})


def resend_passwordreset_otp(request):
    """Resend password reset OTP to email (AJAX)"""
    email = request.session.get('reset_email')
    if not email:
        return JsonResponse({'success': False, 'message': 'Session expired. Please start password reset again.'})
    try:
        user = User.objects.get(email=email)
        # Generate new OTP
        otp_instance = PasswordResetOTP.generate_otp(user)
        # Print OTP to console for debugging (local development only)
        if settings.DEBUG:
            print(f"\n{'='*70}")
            print(f"{' '*18}RESEND PASSWORD RESET OTP")
            print(f"{'='*70}")
            print(f"Email: {email}")
            print(f"{'='*70}")
            print(f"{' '*25}OTP CODE: {otp_instance.otp_code}")
            print(f"{'='*70}")
            print(f"Expires at: {otp_instance.expires_at}")
            print(f"{'='*70}\n")
        # Send email
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@jannatbeauty.com')
        send_mail(
            subject='Password Reset OTP - Jannat Beauty',
            message=f'''Hello,\n\nYour new OTP is: {otp_instance.otp_code}\n\nThis OTP will expire in 10 minutes.\n\nBest regards,\nJannat Beauty Team''',
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        return JsonResponse({'success': True, 'message': f'New OTP sent to {email}.'})
    except Exception as e:
        import traceback
        if settings.DEBUG:
            print(f"\n{'='*60}")
            print(f"ERROR RESENDING PASSWORD RESET OTP:")
            print(f"Error: {str(e)}")
            traceback.print_exc()
            print(f"{'='*60}\n")
        return JsonResponse({'success': False, 'message': f'Failed to resend OTP: {str(e)}'})


def verify_registration_otp(request):
    """Verify registration OTP and create user account"""
    email = request.session.get('registration_email')
    password = request.session.get('registration_password')
    
    if not email or not password:
        messages.error(request, 'Session expired. Please start registration again.')
        return redirect('accounts:register_customer')
    
    # Get the latest valid OTP for debugging (development only)
    debug_otp = None
    try:
        latest_otp = RegistrationOTP.objects.filter(
            email=email,
            is_used=False
        ).order_by('-created_at').first()
        
        if latest_otp and latest_otp.is_valid():
            debug_otp = latest_otp.otp_code
            # Also print to console (local development only)
            if settings.DEBUG:
                print(f"\n{'='*70}")
                print(f"{' '*15}CURRENT VALID REGISTRATION OTP")
                print(f"{'='*70}")
                print(f"Email: {email}")
                print(f"{'='*70}")
                print(f"{' '*25}OTP CODE: {debug_otp}")
                print(f"{'='*70}")
                print(f"Expires at: {latest_otp.expires_at}")
                print(f"{'='*70}\n")
    except Exception:
        pass
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp') or request.POST.get('otp_code')
        
        # Print verification attempt (local development only)
        if settings.DEBUG:
            print(f"\n{'='*70}")
            print(f"{' '*15}REGISTRATION OTP VERIFICATION ATTEMPT")
            print(f"{'='*70}")
            print(f"Email: {email}")
            print(f"OTP Entered: {otp_code}")
            print(f"Expected OTP: {debug_otp}")
            print(f"{'='*70}\n")
        
        try:
            otp_instance = RegistrationOTP.objects.filter(
                email=email,
                otp_code=otp_code,
                is_used=False
            ).first()
            
            if otp_instance and otp_instance.is_valid():
                # Mark OTP as used
                otp_instance.mark_as_used()
                
                # Check if user already exists with this email
                existing_user = User.objects.filter(email=email).first()
                
                if existing_user:
                    # User already exists, just log them in
                    user = existing_user
                    # Ensure profile exists
                    if not hasattr(user, 'profile'):
                        Profile.objects.create(
                            user=user,
                            role='customer'
                        )
                else:
                    # Create new user account
                    username = email.split('@')[0]  # Use email prefix as username
                    # Ensure username is unique
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                    
                    # Create profile only if it doesn't exist
                    if not hasattr(user, 'profile'):
                        Profile.objects.create(
                            user=user,
                            role='customer'
                        )
                
                # Clear session data
                request.session.pop('registration_email', None)
                request.session.pop('registration_password', None)
                
                # Log the user in
                login(request, user)
                
                messages.success(request, 'Account created successfully! Welcome to Jannat Beauty.')
                return redirect('accounts:customer_dashboard')
            else:
                messages.error(request, 'Invalid or expired OTP.')
                
        except Exception as e:
            import traceback
            if settings.DEBUG:
                print(f"\n{'='*60}")
                print(f"ERROR VERIFYING REGISTRATION OTP:")
                print(f"Error: {str(e)}")
                traceback.print_exc()
                print(f"{'='*60}\n")
            messages.error(request, f'An error occurred: {str(e)}')
    
    context = {
        'email': email,
        'debug_otp': debug_otp if settings.DEBUG else None
    }
    return render(request, 'accounts/verify_registration_otp.html', context)


def register_seller(request):
    """Seller registration with business details"""
    if settings.DEBUG:
        print(f"\n{'='*60}")
        print(f"REGISTER_SELLER VIEW CALLED - Method: {request.method}")
        print(f"{'='*60}\n")
    
    try:
        if request.method == 'POST':
            # Auto-generate username from email if not provided
            post_data = request.POST.copy()
            if not post_data.get('username'):
                email = post_data.get('email', '').strip()
                if email:
                    # Generate username from email (part before @)
                    username = email.split('@')[0]
                    # Clean username - remove any invalid characters
                    username = ''.join(c for c in username if c.isalnum() or c in ['_', '-'])
                    if not username:  # If username is empty after cleaning, use a default
                        username = 'seller'
                    # Ensure username is unique
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    post_data['username'] = username
            
            form = SellerRegistrationForm(post_data)
            if form.is_valid():
                user = form.save()
                # Ensure email is saved (it should be, but double-check)
                if not user.email:
                    user.email = form.cleaned_data.get('email')
                    user.save()
                messages.success(request, f'Seller account created! Your account is pending approval.')
                return redirect('accounts:login')
            else:
                # Display form errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            # GET request - just show the form
            if settings.DEBUG:
                print(f"Creating empty SellerRegistrationForm...")
            form = SellerRegistrationForm()
            if settings.DEBUG:
                print(f"Form created successfully. Rendering template...")
        
        return render(request, 'accounts/register_seller.html', {'form': form})
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"\n{'='*60}")
        print(f"ERROR IN REGISTER_SELLER VIEW:")
        print(f"Error: {str(e)}")
        print(f"Traceback:")
        traceback.print_exc()
        print(f"{'='*60}\n")
        messages.error(request, f'An error occurred. Please try again. Error: {str(e)}')
        try:
            form = SellerRegistrationForm()
            return render(request, 'accounts/register_seller.html', {'form': form})
        except Exception as e2:
            print(f"CRITICAL: Could not even create form. Error: {str(e2)}")
            return render(request, 'accounts/register_seller.html', {'form': None})


def user_login(request):
    """Login view - accepts email or username - redirects to appropriate dashboard"""
    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Check if input is an email (contains @)
        if '@' in username_or_email:
            # Try to find user by email
            try:
                user_by_email = User.objects.get(email=username_or_email)
                username = user_by_email.username
            except User.DoesNotExist:
                username = None
        else:
            # Use as username
            username = username_or_email
        
        # Authenticate user
        if username:
            user = authenticate(request, username=username, password=password)
        else:
            user = None
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect based on user type
            if hasattr(user, 'profile') and user.profile.is_seller:
                return redirect('accounts:seller_dashboard')
            else:
                return redirect('accounts:customer_dashboard')
        else:
            messages.error(request, 'Invalid email/username or password.')
    
    return render(request, 'accounts/login.html')


def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('store:home')


# ============================================================================
# CUSTOMER VIEWS
# ============================================================================

@login_required
def customer_dashboard(request):
    """Main customer dashboard with accordion sections"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    if request.user.profile.is_seller:
        messages.error(request, 'Access denied. This is a customer-only area.')
        return redirect('accounts:seller_dashboard')
    
    # Get customer data
    orders = Order.objects.filter(user=request.user).order_by('-created')[:10]
    
    # Get notifications
    notifications = []
    if hasattr(request.user, 'notifications'):
        # Notification model usually uses `created`; some installs may use `created_at`.
        # Try ordering by the canonical `created` first, then fall back to `created_at`.
        try:
            notifications = request.user.notifications.all().order_by('-created')[:10]
        except FieldError:
            # Fallback for different notification implementations
            notifications = request.user.notifications.all().order_by('-created_at')[:10]
    
    context = {
        'orders': orders,
        'notifications': notifications,
        'profile': request.user.profile,
        'current_page': 'home',
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@login_required
def customer_profile(request):
    """Customer profile edit"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    if request.user.profile.is_seller:
        messages.error(request, 'Access denied. This is a customer-only area.')
        return redirect('accounts:seller_dashboard')
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:customer_dashboard')
    else:
        form = ProfileUpdateForm(instance=request.user.profile, user=request.user)
    
    context = {
        'form': form,
        'profile': request.user.profile,
        'current_page': 'profile',
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@login_required
def customer_orders(request):
    """Customer order history"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    if request.user.profile.is_seller:
        messages.error(request, 'Access denied. This is a customer-only area.')
        return redirect('accounts:seller_dashboard')
    
    orders = Order.objects.filter(user=request.user).order_by('-created')
    
    context = {
        'orders': orders,
        'profile': request.user.profile,
        'current_page': 'orders',
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@login_required
def customer_notifications(request):
    """Customer notifications"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    if request.user.profile.is_seller:
        messages.error(request, 'Access denied. This is a customer-only area.')
        return redirect('accounts:seller_dashboard')
    
    notifications = []
    if hasattr(request.user, 'notifications'):
        # Notification model usually uses `created`; some installs may use `created_at`.
        try:
            notifications = request.user.notifications.all().order_by('-created')
        except FieldError:
            notifications = request.user.notifications.all().order_by('-created_at')
    
    context = {
        'notifications': notifications,
        'profile': request.user.profile,
        'current_page': 'notifications',
    }
    return render(request, 'accounts/customer_dashboard.html', context)


@login_required
def customer_addresses(request):
    """Customer saved addresses"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    if request.user.profile.is_seller:
        messages.error(request, 'Access denied. This is a customer-only area.')
        return redirect('accounts:seller_dashboard')
    
    context = {
        'profile': request.user.profile,
        'current_page': 'addresses',
    }
    return render(request, 'accounts/customer_dashboard.html', context)


# ============================================================================
# SELLER VIEWS
# ============================================================================

@login_required
def seller_dashboard(request):
    """Main seller dashboard"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Seller account required.')
        return redirect('accounts:customer_dashboard')
    
    try:
        seller_profile = request.user.seller_profile
    except SellerProfile.DoesNotExist:
        messages.error(request, 'Seller profile not found. Please contact support.')
        return redirect('store:home')
    
    # Check approval status
    if not seller_profile.is_approved:
        messages.warning(request, f'Your seller account is {seller_profile.get_approval_status_display()}.')
    
    # Get seller's products (optimized query)
    products = request.user.products.select_related('category')[:10] if hasattr(request.user, 'products') else []
    
    # Get seller's orders (optimized with select_related and prefetch_related)
    order_items = OrderItem.objects.filter(
        product__seller=request.user
    ).select_related('order', 'product', 'order__user')
    
    orders = Order.objects.filter(
        items__product__seller=request.user
    ).distinct().select_related('user').prefetch_related('items', 'items__product')
    
    # Calculate analytics (optimized - combine aggregations)
    total_products = request.user.products.count() if hasattr(request.user, 'products') else 0
    
    # Single query for sales and revenue
    sales_data = order_items.aggregate(
        total_sales=models.Sum('quantity'),
        total_revenue=models.Sum(models.F('price') * models.F('quantity'))
    )
    total_sales = sales_data['total_sales'] or 0
    total_revenue = sales_data['total_revenue'] or 0
    
    # Optimize order counts
    order_counts = orders.aggregate(
        total_orders=models.Count('id'),
        pending_orders=models.Count('id', filter=models.Q(order_status='pending')),
        pending_shipments=models.Count('id', filter=models.Q(paid=True, shiprocket_order_id__isnull=True))
    )
    total_orders = order_counts['total_orders'] or 0
    pending_orders = order_counts['pending_orders'] or 0
    pending_shipments = order_counts['pending_shipments'] or 0
    
    context = {
        'seller_profile': seller_profile,
        'products': products,
        'order_items': order_items[:20],
        'total_products': total_products,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'pending_shipments': pending_shipments,
    }
    return render(request, 'accounts/seller_dashboard.html', context)


@login_required
def seller_products(request):
    """Seller products management"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Seller account required.')
        return redirect('accounts:customer_dashboard')
    
    products = request.user.products.all() if hasattr(request.user, 'products') else []
    
    context = {
        'products': products,
        'seller_profile': request.user.seller_profile,
    }
    return render(request, 'accounts/seller_products.html', context)


@login_required
def seller_orders(request):
    """Seller orders management"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Seller account required.')
        return redirect('accounts:customer_dashboard')
    
    order_items = OrderItem.objects.filter(product__seller=request.user).select_related('order', 'product').order_by('-order__created')
    
    context = {
        'order_items': order_items,
        'seller_profile': request.user.seller_profile,
    }
    return render(request, 'accounts/seller_orders.html', context)


@login_required
def seller_analytics(request):
    """Seller analytics and insights"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Seller account required.')
        return redirect('accounts:customer_dashboard')
    
    order_items = OrderItem.objects.filter(product__seller=request.user)
    orders = Order.objects.filter(items__product__seller=request.user).distinct()
    
    # Calculate detailed analytics
    analytics = {
        'total_sales': order_items.aggregate(total=models.Sum('quantity'))['total'] or 0,
        'total_revenue': order_items.aggregate(
            total=models.Sum(models.F('price') * models.F('quantity'))
        )['total'] or 0,
        'total_orders': orders.count(),
        'pending_orders': orders.filter(order_status='pending').count(),
        'completed_orders': orders.filter(order_status='completed').count(),
        'average_order_value': 0,
    }
    
    if analytics['total_orders'] > 0:
        analytics['average_order_value'] = analytics['total_revenue'] / analytics['total_orders']
    
    context = {
        'analytics': analytics,
        'seller_profile': request.user.seller_profile,
    }
    return render(request, 'accounts/seller_analytics.html', context)


@login_required
def seller_profile(request):
    """Seller profile view and edit"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Seller account required.')
        return redirect('accounts:customer_dashboard')
    
    try:
        seller_profile = request.user.seller_profile
    except SellerProfile.DoesNotExist:
        messages.error(request, 'Seller profile not found.')
        return redirect('store:home')
    
    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile, user=request.user)
        seller_form = SellerProfileUpdateForm(request.POST, instance=seller_profile)
        
        if profile_form.is_valid() and seller_form.is_valid():
            profile_form.save()
            seller_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:seller_dashboard')
    else:
        profile_form = ProfileUpdateForm(instance=request.user.profile, user=request.user)
        seller_form = SellerProfileUpdateForm(instance=seller_profile)
    
    context = {
        'profile_form': profile_form,
        'seller_form': seller_form,
        'seller_profile': seller_profile,
    }
    return render(request, 'accounts/seller_profile.html', context)


# ============================================================================
# PASSWORD RESET VIEWS
# ============================================================================

def forgot_password(request):
    """Send OTP to user's email for password reset"""
    if request.user.is_authenticated:
        return redirect('accounts:customer_dashboard')
    
    # Debug: Print request method
    print(f"\n{'='*60}")
    print(f"FORGOT PASSWORD REQUEST: {request.method}")
    print(f"{'='*60}\n")
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        print(f"\n{'='*60}")
        print(f"FORM SUBMITTED - Email received: {email}")
        print(f"All POST data: {dict(request.POST)}")
        print(f"{'='*60}\n")
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'accounts/forgot_password.html')
        
        try:
            user = User.objects.get(email=email)
            print(f"User found: {user.username} ({user.email})")
            
            # Generate OTP
            otp_instance = PasswordResetOTP.generate_otp(user)
            
            # Print OTP to console for debugging (local development only)
            if settings.DEBUG:
                print(f"\n{'='*70}")
                print(f"{' '*18}PASSWORD RESET OTP GENERATED")
                print(f"{'='*70}")
                print(f"Email: {email}")
                print(f"{'='*70}")
                print(f"{' '*25}OTP CODE: {otp_instance.otp_code}")
                print(f"{'='*70}")
                print(f"Expires at: {otp_instance.expires_at}")
                print(f"{'='*70}\n")
            
            # Send email with OTP
            try:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@jannatbeauty.com')
                if settings.DEBUG:
                    print(f"Sending email from: {from_email}")
                
                send_mail(
                    subject='Password Reset OTP - Jannat Beauty',
                    message=f'''Hello {user.first_name or user.username},

You requested a password reset for your account.

Your OTP is: {otp_instance.otp_code}

This OTP will expire in 10 minutes.

If you didn't request this, please ignore this email.

Best regards,
Jannat Beauty Team''',
                    from_email=from_email,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                if settings.DEBUG:
                    print(f"Email sent successfully!")
                
                # Store email in session for next step
                request.session['reset_email'] = email
                messages.success(request, f'OTP has been sent to {email}. Please check your inbox or console.')
                return redirect('accounts:verify_otp')
                
            except Exception as e:
                # Log the error for debugging
                import traceback
                if settings.DEBUG:
                    print(f"\n{'='*60}")
                    print(f"ERROR SENDING EMAIL:")
                    print(f"Error: {str(e)}")
                    print(f"Traceback:")
                    traceback.print_exc()
                    print(f"{'='*60}\n")
                messages.error(request, f'Failed to send OTP. Error: {str(e)}. Check console for OTP: {otp_instance.otp_code}')
                
        except User.DoesNotExist:
            if settings.DEBUG:
                print(f"User with email {email} does not exist in database")
            # Don't reveal if email exists for security
            messages.success(request, 'If an account exists with this email, an OTP has been sent.')
    
    return render(request, 'accounts/forgot_password.html')


def verify_otp(request):
    """Verify OTP and allow password reset"""
    email = request.session.get('reset_email')
    
    if not email:
        messages.error(request, 'Session expired. Please start the password reset process again.')
        return redirect('accounts:forgot_password')
    
    # Get the latest valid OTP for debugging (development only)
    debug_otp = None
    try:
        user = User.objects.get(email=email)
        latest_otp = PasswordResetOTP.objects.filter(
            user=user,
            email=email,
            is_used=False
        ).order_by('-created_at').first()
        
        if latest_otp and latest_otp.is_valid():
            debug_otp = latest_otp.otp_code
            # Also print to console (local development only)
            if settings.DEBUG:
                print(f"\n{'='*70}")
                print(f"{' '*20}CURRENT VALID OTP")
                print(f"{'='*70}")
                print(f"Email: {email}")
                print(f"{'='*70}")
                print(f"{' '*25}OTP CODE: {debug_otp}")
                print(f"{'='*70}")
                print(f"Expires at: {latest_otp.expires_at}")
                print(f"{'='*70}\n")
    except User.DoesNotExist:
        pass
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp') or request.POST.get('otp_code')
        
        # Print verification attempt (local development only)
        if settings.DEBUG:
            print(f"\n{'='*70}")
            print(f"{' '*20}OTP VERIFICATION ATTEMPT")
            print(f"{'='*70}")
            print(f"Email: {email}")
            print(f"OTP Entered: {otp_code}")
            print(f"Expected OTP: {debug_otp}")
            print(f"{'='*70}\n")
        
        try:
            user = User.objects.get(email=email)
            otp_instance = PasswordResetOTP.objects.filter(
                user=user,
                email=email,
                otp_code=otp_code,
                is_used=False
            ).first()
            
            if otp_instance and otp_instance.is_valid():
                # Mark OTP as used
                otp_instance.mark_as_used()
                
                # Store verification in session
                request.session['otp_verified'] = True
                request.session['reset_user_id'] = user.id
                
                messages.success(request, 'OTP verified successfully. You can now reset your password.')
                return redirect('accounts:reset_password')
            else:
                messages.error(request, 'Invalid or expired OTP.')
                
        except User.DoesNotExist:
            messages.error(request, 'Invalid request.')
            return redirect('accounts:forgot_password')
    
    context = {
        'email': email,
        'debug_otp': debug_otp if settings.DEBUG else None
    }
    return render(request, 'accounts/verify_otp.html', context)


def reset_password(request):
    """Reset password after OTP verification"""
    if not request.session.get('otp_verified') or not request.session.get('reset_user_id'):
        messages.error(request, 'Please verify OTP first.')
        return redirect('accounts:forgot_password')
    
    if request.method == 'POST':
        if settings.DEBUG:
            print(f"\n{'='*60}")
            print(f"RESET PASSWORD POST - All POST data: {dict(request.POST)}")
            print(f"{'='*60}\n")
        
        # Check for both possible field names (password1/password2 or new_password1/new_password2)
        password1 = request.POST.get('new_password1', '').strip() or request.POST.get('password1', '').strip()
        password2 = request.POST.get('new_password2', '').strip() or request.POST.get('password2', '').strip()
        
        if settings.DEBUG:
            print(f"Password1 received: {'Yes' if password1 else 'No'} (length: {len(password1) if password1 else 0})")
            print(f"Password2 received: {'Yes' if password2 else 'No'} (length: {len(password2) if password2 else 0})")
        
        if not password1:
            messages.error(request, 'Please enter a password.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            try:
                user_id = request.session.get('reset_user_id')
                user = User.objects.get(id=user_id)
                user.set_password(password1)
                user.save()
                
                # Clear session data
                request.session.pop('otp_verified', None)
                request.session.pop('reset_user_id', None)
                request.session.pop('reset_email', None)
                
                messages.success(request, 'Password reset successfully. You can now log in.')
                return redirect('accounts:login')
                
            except User.DoesNotExist:
                messages.error(request, 'Invalid request.')
                return redirect('accounts:forgot_password')
    
    return render(request, 'accounts/reset_password.html')
