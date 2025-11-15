from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from .models import Category, Product
from .forms import ProductForm
from accounts.models import SellerProfile


def about_page(request):
    return render(request, 'store/about.html')


def product_list(request, category_slug=None):
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        from django.contrib import messages
        messages.error(request, 'Sellers cannot browse products.')
        return redirect('accounts:seller_dashboard')
    
    category = None
    categories = Category.objects.all()
    
    # Only show approved products from approved sellers
    products = Product.objects.filter(
        available=True,
        approved=True,
        seller__seller_profile__approval_status='approved'
    )
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    # Price filtering
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Featured filter
    featured = request.GET.get('featured')
    if featured == 'true':
        products = products.filter(featured=True)
    
    # Stock filter
    in_stock = request.GET.get('in_stock')
    if in_stock == 'true':
        products = products.filter(stock__gt=0)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    valid_sorts = ['name', '-name', 'price', '-price', 'created', '-created']
    if sort_by in valid_sorts:
        products = products.order_by(sort_by)
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page = request.GET.get('page')
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
        'sort_by': sort_by,
    }
    return render(request, 'store/product/list.html', context)


def product_detail(request, slug):
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        from django.contrib import messages
        messages.error(request, 'Sellers cannot view product details.')
        return redirect('accounts:seller_dashboard')
    
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(
        category=product.category, 
        available=True
    ).exclude(id=product.id)[:4]
    
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
    
    # Only surface approved products from approved sellers on the homepage
    featured_products = Product.objects.filter(
        featured=True,
        available=True,
        approved=True,
        seller__seller_profile__approval_status='approved'
    )[:8]
    latest_products = Product.objects.all().order_by('-created')[:8]
    categories = Category.objects.all()[:6]
    
    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)


@login_required
def add_product(request):
    """View for sellers to add new products"""
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
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            # Products created by sellers need approval (unless they're admins)
            product.approved = request.user.is_superuser
            product.save()
            
            if request.user.is_superuser:
                messages.success(request, f'Product "{product.name}" added successfully!')
            else:
                messages.success(request, f'Product "{product.name}" added successfully! It will be visible after admin approval.')
            
            return redirect('accounts:seller_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()

    context = {
        'form': form,
        'is_admin': request.user.is_superuser,
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
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            if request.user.is_superuser:
                return redirect('admin:store_product_changelist')
            return redirect('accounts:seller_dashboard')
    else:
        form = ProductForm(instance=product)

    return render(request, 'store/edit_product.html', {'form': form, 'product': product})


@login_required
def delete_product(request, product_id):
    """View for sellers to delete their products"""
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
            messages.success(request, f'Product "{product.name}" has been approved!')
        elif action == 'disapprove':
            product.approved = False
            product.save()
            messages.success(request, f'Product "{product.name}" has been disapproved!')
    
    return redirect('store:admin_manage_products')
