from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.conf import settings
from .models import Category, Product
from .forms import ProductForm
from accounts.models import SellerProfile


class HealthCheckView(View):
    """
    Health check endpoint for monitoring deployment status
    Returns JSON with system status information
    """
    
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'database': self.check_database(),
            'cache': self.check_cache(),
            'debug': settings.DEBUG,
            'environment': 'production' if not settings.DEBUG else 'development'
        }
        
        # Determine overall status
        if not health_status['database']['healthy']:
            health_status['status'] = 'unhealthy'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return JsonResponse(health_status, status=status_code)
    
    def check_database(self):
        """Check database connectivity"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {'healthy': True, 'message': 'Database connection successful'}
        except Exception as e:
            return {'healthy': False, 'message': f'Database error: {str(e)}'}
    
    def check_cache(self):
        """Check cache connectivity (Redis or local memory)"""
        try:
            # Test cache set/get
            test_key = 'health_check_test'
            test_value = 'test_value'
            cache.set(test_key, test_value, timeout=60)
            retrieved = cache.get(test_key)
            
            if retrieved == test_value:
                cache.delete(test_key)  # Cleanup
                cache_backend = settings.CACHES['default']['BACKEND']
                return {
                    'healthy': True, 
                    'message': f'Cache working: {cache_backend.split(".")[-1]}'
                }
            else:
                return {'healthy': False, 'message': 'Cache set/get failed'}
        except Exception as e:
            return {'healthy': False, 'message': f'Cache error: {str(e)}'}


def about_page(request):
    return render(request, 'store/about.html')


def product_list(request, category_slug=None):
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        from django.contrib import messages
        messages.error(request, 'Sellers cannot browse products.')
        return redirect('accounts:seller_dashboard')
    
    # Build cache key based on filters
    query = request.GET.get('q', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    featured = request.GET.get('featured', '')
    in_stock = request.GET.get('in_stock', '')
    major_category = request.GET.get('major_category', '')
    sort_by = request.GET.get('sort', 'name')
    page = request.GET.get('page', '1')
    
    # Only cache if no search/filters to avoid stale results
    use_cache = not query and not min_price and not max_price and not featured and not in_stock
    
    category = None
    # Cache categories list (they don't change often)
    categories = cache.get('all_categories')
    if categories is None:
        categories = Category.objects.all()
        cache.set('all_categories', categories, 60 * 60)  # Cache for 1 hour
    
    # Only show approved products from approved sellers (optimized query)
    products = Product.objects.filter(
        available=True,
        approved=True,
        seller__seller_profile__approval_status='approved'
    ).select_related('category', 'seller', 'seller__seller_profile')
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category).select_related('category')
    
    # Search functionality
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    # Price filtering
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Featured filter
    if featured == 'true':
        products = products.filter(featured=True)
    
    # Stock filter
    if in_stock == 'true':
        products = products.filter(stock__gt=0)
    
    # Major category filter (new_arrivals, featured, best_selling)
    if major_category:
        valid_major_categories = ['new_arrivals', 'featured', 'best_selling']
        if major_category in valid_major_categories:
            products = products.filter(major_category=major_category)
    
    # Sorting
    valid_sorts = ['name', '-name', 'price', '-price', 'created', '-created']
    if sort_by in valid_sorts:
        products = products.order_by(sort_by)
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
        'featured': featured,
        'in_stock': in_stock,
        'major_category': major_category,
        'sort_by': sort_by,
    }
    
    return render(request, 'store/product/list.html', context)


def product_detail(request, slug):
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        from django.contrib import messages
        messages.error(request, 'Sellers cannot view product details.')
        return redirect('accounts:seller_dashboard')
    
    # Cache product detail
    cache_key = f'product_detail_{slug}'
    cached_product = cache.get(cache_key)
    
    if cached_product:
        product = cached_product
    else:
        product = get_object_or_404(
            Product.objects.select_related('category', 'seller', 'seller__seller_profile')
            .prefetch_related('reviews', 'images'),
            slug=slug,
            available=True
        )
        cache.set(cache_key, product, 60 * 30)  # Cache for 30 minutes
    
    # Cache related products
    related_cache_key = f'related_products_{product.category_id}_{product.id}'
    related_products = cache.get(related_cache_key)
    
    if related_products is None:
        related_products = Product.objects.filter(
            category=product.category, 
            available=True,
            approved=True
        ).select_related('category', 'seller').exclude(id=product.id)[:4]
        cache.set(related_cache_key, list(related_products), 60 * 30)  # Cache for 30 minutes
    
    # Get reviews data
    reviews = product.reviews.all() if hasattr(product, 'reviews') else []
    average_rating = 0
    if reviews:
        from django.db.models import Avg
        avg = reviews.aggregate(Avg('rating'))['rating__avg']
        average_rating = avg if avg else 0
    
    # Check if user has already reviewed
    user_has_reviewed = False
    if request.user.is_authenticated and reviews:
        user_has_reviewed = reviews.filter(user=request.user).exists()
    
    context = {
        'product': product,
        'related_products': related_products,
        'average_rating': average_rating,
        'user_has_reviewed': user_has_reviewed,
    }
    return render(request, 'store/product/detail.html', context)


def home(request):
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        from django.contrib import messages
        messages.error(request, 'Sellers cannot access the main store.')
        return redirect('accounts:seller_dashboard')
    
    # Cache home page data
    new_arrivals = cache.get('home_new_arrivals')
    if new_arrivals is None:
        new_arrivals = Product.objects.filter(
            major_category='new_arrivals',
            available=True,
            approved=True,
            seller__seller_profile__approval_status='approved'
        ).select_related('category', 'seller').order_by('-created')[:8]
        cache.set('home_new_arrivals', list(new_arrivals), 60 * 15)  # Cache for 15 minutes
    
    featured_products = cache.get('home_featured_products')
    if featured_products is None:
        featured_products = Product.objects.filter(
            major_category='featured',
            available=True,
            approved=True,
            seller__seller_profile__approval_status='approved'
        ).select_related('category', 'seller').order_by('-created')[:8]
        cache.set('home_featured_products', list(featured_products), 60 * 15)  # Cache for 15 minutes
    
    best_selling_products = cache.get('home_best_selling_products')
    if best_selling_products is None:
        best_selling_products = Product.objects.filter(
            major_category='best_selling',
            available=True,
            approved=True,
            seller__seller_profile__approval_status='approved'
        ).select_related('category', 'seller').order_by('-created')[:8]
        cache.set('home_best_selling_products', list(best_selling_products), 60 * 15)  # Cache for 15 minutes
    
    categories = cache.get('home_categories')
    if categories is None:
        categories = Category.objects.all()[:6]
        cache.set('home_categories', list(categories), 60 * 60)  # Cache for 1 hour

    context = {
        'new_arrivals': new_arrivals,
        'featured_products': featured_products,
        'best_selling_products': best_selling_products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import json
from .models import Lead


@csrf_exempt
def submit_lead(request):
    """Handle lead submission from discount popup"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            
            if not name or not phone:
                return JsonResponse({
                    'success': False, 
                    'message': 'Please provide both name and phone number.'
                })
            
            # Create lead record
            lead = Lead.objects.create(
                name=name,
                mobile=phone
            )
            
            # Send email to admin
            try:
                subject = f'New Lead: {name} - 10% Discount Offer'
                message = f'''
New lead has been submitted from the discount popup:

Name: {name}
Mobile: {phone}
Date: {lead.created.strftime("%Y-%m-%d %H:%M:%S")}

This lead is interested in the 10% discount offer.
You can view this lead in the admin dashboard.
                '''
                
                # Get admin email from settings or use default
                admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [admin_email],
                    fail_silently=False,
                )
                
                lead.email_sent = True
                lead.save()
                
            except Exception as e:
                # Log error but don't fail the request
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error sending lead email: {str(e)}')
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you! Your details have been submitted. You will receive your 10% discount code shortly.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid data format.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Something went wrong. Please try again.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def add_product(request):
    """View for sellers to add new products"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    # Check if user is a seller or admin
    if not request.user.profile.is_seller and not request.user.is_superuser:
        messages.error(request, 'Access denied. Only sellers can add products.')
        return redirect('store:home')

    # For sellers, check if seller profile exists and is approved
    if request.user.profile.is_seller:
        try:
            seller_profile = request.user.seller_profile
            if not seller_profile.can_sell:
                messages.error(request, 'Your seller account is not approved. Please wait for approval.')
                return redirect('accounts:seller_dashboard')
        except SellerProfile.DoesNotExist:
            messages.error(request, 'Seller profile not found. Please complete your seller registration.')
            return redirect('accounts:customer_profile')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            
            # Check if seller is approved or is superuser
            is_seller_approved = False
            if not request.user.is_superuser:
                try:
                    seller_profile = request.user.seller_profile
                    is_seller_approved = seller_profile.is_approved
                except SellerProfile.DoesNotExist:
                    is_seller_approved = False
            
            # Validate major category permission if seller is adding
            if not request.user.is_superuser and hasattr(request.user, 'seller_profile'):
                try:
                    seller_profile = request.user.seller_profile
                    major_category = form.cleaned_data.get('major_category', 'none')
                    if major_category and not seller_profile.can_manage_major_category(major_category):
                        messages.error(request, f'You do not have permission to use the "{dict(Product.MAJOR_CATEGORY_CHOICES).get(major_category, major_category)}" major category.')
                        form = ProductForm(user=request.user)
                        context = {
                            'form': form,
                            'is_admin': request.user.is_superuser,
                            'product': None,
                        }
                        return render(request, 'store/add_product.html', context)
                except Exception as e:
                    pass
            
            # Auto-approve products from approved sellers or superusers
            product.approved = request.user.is_superuser or is_seller_approved
            product.save()
            
            # Handle extra images upload
            from .models import ProductImage
            extra_images = request.FILES.getlist('extra_images')
            for img_file in extra_images:
                ProductImage.objects.create(product=product, image=img_file)
            
            if request.user.is_superuser or is_seller_approved:
                messages.success(request, f'Product "{product.name}" added successfully and is now live!')
            else:
                messages.success(request, f'Product "{product.name}" added successfully! It will be visible after admin approval.')
            
            return redirect('accounts:seller_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(user=request.user)

    context = {
        'form': form,
        'is_admin': request.user.is_superuser,
        'product': None,
    }
    return render(request, 'store/add_product.html', context)


@login_required
def edit_product(request, product_id):
    """View for sellers to edit their products"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user owns this product or is superuser
    if product.seller != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied. You can only edit your own products.')
        return redirect('accounts:seller_dashboard')
    
    # Check seller status
    if not request.user.is_superuser and not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Only sellers can edit products.')
        return redirect('store:home')
    
    if not request.user.is_superuser:
        try:
            seller_profile = request.user.seller_profile
            if not seller_profile.can_sell:
                messages.error(request, 'Access denied. Your seller account is not approved.')
                return redirect('accounts:seller_dashboard')
        except SellerProfile.DoesNotExist:
            messages.error(request, 'Seller profile not found.')
            return redirect('accounts:customer_profile')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, user=request.user)
        if form.is_valid():
            # Validate major category permission if seller is editing
            if not request.user.is_superuser and hasattr(request.user, 'seller_profile'):
                try:
                    seller_profile = request.user.seller_profile
                    major_category = form.cleaned_data.get('major_category', 'none')
                    if major_category and not seller_profile.can_manage_major_category(major_category):
                        messages.error(request, f'You do not have permission to use the "{dict(Product.MAJOR_CATEGORY_CHOICES).get(major_category, major_category)}" major category.')
                        form = ProductForm(instance=product, user=request.user)
                        return render(request, 'store/edit_product.html', {'form': form, 'product': product})
                except Exception as e:
                    pass
            
            form.save()
            
            # Handle extra images upload
            from .models import ProductImage
            extra_images = request.FILES.getlist('extra_images')
            for img_file in extra_images:
                ProductImage.objects.create(product=product, image=img_file)
            
            messages.success(request, 'Product updated successfully!')
            if request.user.is_superuser:
                return redirect('admin:store_product_changelist')
            return redirect('accounts:seller_dashboard')
    else:
        form = ProductForm(instance=product, user=request.user)

    return render(request, 'store/edit_product.html', {'form': form, 'product': product})


@login_required
def delete_product(request, product_id):
    """View for sellers to delete their products"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('store:home')
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user owns this product or is superuser
    if product.seller != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied. You can only delete your own products.')
        return redirect('accounts:seller_dashboard')
    
    # Check seller status
    if not request.user.is_superuser and not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Only sellers can delete products.')
        return redirect('store:home')

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        if request.user.is_superuser:
            return redirect('admin:store_product_changelist')
        return redirect('accounts:seller_dashboard')

    return render(request, 'store/delete_product.html', {'product': product})


@login_required
def delete_product_image(request, product_id, image_id):
    """View for sellers to delete product images"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user owns this product or is superuser
    if product.seller != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied. You can only delete images from your own products.')
        return redirect('accounts:seller_dashboard')
    
    # Get the product image
    from .models import ProductImage
    product_image = get_object_or_404(ProductImage, id=image_id, product=product)
    
    if request.method == 'POST':
        product_image.delete()
        messages.success(request, 'Image deleted successfully!')
    
    return redirect('store:edit_product', product_id=product.id)


@login_required
def seller_products(request):
    """View for sellers to manage their products"""
    if not request.user.profile.is_seller:
        messages.error(request, 'Access denied. Only sellers can access this page.')
        return redirect('store:home')
    
    products = Product.objects.filter(seller=request.user).order_by('-created')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(products, 10)  # Show 10 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except:
        products = paginator.page(1)
    
    context = {
        'products': products,
        'total_products': Product.objects.filter(seller=request.user).count()
    }
    return render(request, 'store/seller_products.html', context)


@login_required
def admin_add_product(request):
    """View for superuser to add products with full control"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('store:home')

    if request.method == 'POST':
        from .forms import AdminProductForm
        form = AdminProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" added successfully!')
            return redirect('store:manage_sellers')
    else:
        from .forms import AdminProductForm
        form = AdminProductForm()

    return render(request, 'store/admin_add_product.html', {'form': form})


@login_required
def manage_sellers(request):
    """View for superuser to manage all sellers"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('store:home')
    
    from accounts.models import SellerProfile
    from django.db.models import Count, Sum
    
    # Get all sellers with statistics
    sellers = SellerProfile.objects.select_related('user').annotate(
        product_count=Count('user__products'),
        total_sales=Sum('user__products__order_items__quantity')
    ).order_by('-created')
    
    # Handle approval actions
    if request.method == 'POST':
        action = request.POST.get('action')
        seller_id = request.POST.get('seller_id')
        
        try:
            seller_profile = SellerProfile.objects.get(id=seller_id)
            if action == 'approve':
                seller_profile.approval_status = 'approved'
                seller_profile.save()
                messages.success(request, f'Seller "{seller_profile.business_name}" approved successfully!')
            elif action == 'reject':
                seller_profile.approval_status = 'rejected'
                seller_profile.save()
                messages.success(request, f'Seller "{seller_profile.business_name}" rejected.')
            elif action == 'suspend':
                seller_profile.approval_status = 'suspended'
                seller_profile.save()
                messages.success(request, f'Seller "{seller_profile.business_name}" suspended.')
        except SellerProfile.DoesNotExist:
            messages.error(request, 'Seller not found.')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        sellers = sellers.filter(approval_status=status_filter)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(sellers, 20)
    page = request.GET.get('page')
    try:
        sellers = paginator.page(page)
    except:
        sellers = paginator.page(1)
    
    context = {
        'sellers': sellers,
        'status_filter': status_filter,
        'total_sellers': SellerProfile.objects.count(),
        'pending_sellers': SellerProfile.objects.filter(approval_status='pending').count(),
        'approved_sellers': SellerProfile.objects.filter(approval_status='approved').count(),
    }
    
    return render(request, 'store/manage_sellers.html', context)


@login_required
def admin_manage_products(request):
    """View for admin to manage all products and approvals"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('store:home')
    
    # Filter products based on status
    status_filter = request.GET.get('status', 'all')
    products = Product.objects.all().order_by('-created')
    
    if status_filter == 'pending':
        products = products.filter(approved=False)
    elif status_filter == 'approved':
        products = products.filter(approved=True)
    elif status_filter == 'unavailable':
        products = products.filter(available=False)
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(seller__username__icontains=query) |
            Q(seller__seller_profile__business_name__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except:
        products = paginator.page(1)
    
    context = {
        'products': products,
        'status_filter': status_filter,
        'query': query,
        'total_products': Product.objects.count(),
        'pending_products': Product.objects.filter(approved=False).count(),
        'approved_products': Product.objects.filter(approved=True).count(),
    }
    
    return render(request, 'store/admin_manage_products.html', context)


@login_required
def approve_product(request, product_id):
    """View for admin to approve/disapprove products"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('store:home')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            product.approved = True
            product.save()
            # Send approval email to seller
            try:
                from .utils import send_product_approval_email
                send_product_approval_email(product, True)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send product approval email: {str(e)}')
            messages.success(request, f'Product "{product.name}" has been approved!')
        elif action == 'disapprove':
            product.approved = False
            product.save()
            # Send disapproval email to seller
            try:
                from .utils import send_product_approval_email
                send_product_approval_email(product, False)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send product disapproval email: {str(e)}')
            messages.success(request, f'Product "{product.name}" has been disapproved!')
    
    return redirect('store:admin_manage_products')
