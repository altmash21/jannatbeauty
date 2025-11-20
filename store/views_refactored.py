"""
Refactored store views using service layer and type hints.
Expert-level code organization with separation of concerns.
"""
from typing import Optional
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from utils.decorators import customer_required
from utils.logging_config import get_logger, log_view_execution
from .services import ProductService, CategoryService, HomePageService

logger = get_logger(__name__)


def about_page(request: HttpRequest) -> HttpResponse:
    """
    Display about page.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with about page.
    """
    return render(request, 'store/about.html')


@log_view_execution(logger)
def product_list(request: HttpRequest, category_slug: Optional[str] = None) -> HttpResponse:
    """
    Display paginated list of products with filtering and search.
    
    Args:
        request: HTTP request object.
        category_slug: Optional category slug to filter by.
        
    Returns:
        HTTP response with product list page.
    """
    # Check if seller trying to access
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        messages.error(request, 'Sellers cannot browse products.')
        return redirect('accounts:seller_dashboard')
    
    # Get filter parameters
    query = request.GET.get('q', '').strip()
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    featured = request.GET.get('featured', '')
    in_stock = request.GET.get('in_stock', '')
    sort_by = request.GET.get('sort', 'name')
    
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    
    # Get base queryset using service
    products = ProductService.get_approved_products()
    
    # Get category if specified
    category = None
    if category_slug:
        category = CategoryService.get_category_by_slug(category_slug)
        if not category:
            messages.error(request, 'Category not found.')
            return redirect('store:product_list')
        products = products.filter(category=category)
    
    # Apply filters using service
    products = ProductService.search_products(query, products)
    
    # Convert price strings to floats
    min_price_float = float(min_price) if min_price else None
    max_price_float = float(max_price) if max_price else None
    featured_bool = featured == 'true' if featured else None
    in_stock_bool = in_stock == 'true' if in_stock else None
    
    products = ProductService.filter_products(
        products,
        min_price=min_price_float,
        max_price=max_price_float,
        featured=featured_bool,
        in_stock=in_stock_bool
    )
    
    # Sort products
    products = ProductService.sort_products(products, sort_by)
    
    # Paginate
    paginator, products_page = ProductService.paginate_products(products, page, per_page=12)
    
    # Get categories for sidebar
    categories = CategoryService.get_all_categories()
    
    context = {
        'category': category,
        'categories': categories,
        'products': products_page,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
        'featured': featured,
        'in_stock': in_stock,
        'sort_by': sort_by,
    }
    
    return render(request, 'store/product/list.html', context)


@log_view_execution(logger)
@customer_required
def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Display product detail page with reviews and related products.
    
    Args:
        request: HTTP request object.
        slug: Product slug identifier.
        
    Returns:
        HTTP response with product detail page.
    """
    # Get product using service
    product = ProductService.get_product_by_slug(slug)
    
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('store:product_list')
    
    # Get related products
    related_products = ProductService.get_related_products(product, limit=4)
    
    # Get review statistics
    review_stats = ProductService.get_product_reviews_stats(product)
    
    # Check if user has reviewed
    user_has_reviewed = False
    if request.user.is_authenticated and review_stats['reviews']:
        user_has_reviewed = review_stats['reviews'].filter(user=request.user).exists()
    
    context = {
        'product': product,
        'related_products': related_products,
        'average_rating': review_stats['average_rating'],
        'total_reviews': review_stats['total_reviews'],
        'user_has_reviewed': user_has_reviewed,
    }
    
    return render(request, 'store/product/detail.html', context)


@log_view_execution(logger)
def home(request: HttpRequest) -> HttpResponse:
    """
    Display home page with featured products and categories.
    
    Args:
        request: HTTP request object.
        
    Returns:
        HTTP response with home page.
    """
    # Check if seller trying to access
    if hasattr(request.user, 'profile') and request.user.profile.is_seller:
        messages.error(request, 'Sellers cannot access the main store.')
        return redirect('accounts:seller_dashboard')
    
    # Get home page data using service
    context = HomePageService.get_home_page_data()
    
    return render(request, 'store/home.html', context)

