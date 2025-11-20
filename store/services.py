"""
Service layer for store business logic.
Separates business logic from views for better maintainability and testability.
"""
from typing import Optional, Dict, List, Tuple
from django.db.models import Q, QuerySet, Avg, Sum, F
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from .models import Product, Category


class ProductService:
    """Service for product-related business logic."""
    
    @staticmethod
    def get_approved_products() -> QuerySet[Product]:
        """
        Get all approved products from approved sellers.
        
        Returns:
            QuerySet of approved products with optimized queries.
        """
        return Product.objects.filter(
            available=True,
            approved=True,
            seller__seller_profile__approval_status='approved'
        ).select_related('category', 'seller', 'seller__seller_profile')
    
    @staticmethod
    def get_product_by_slug(slug: str) -> Optional[Product]:
        """
        Get a single product by slug with optimized queries.
        
        Args:
            slug: Product slug identifier.
            
        Returns:
            Product instance or None if not found.
        """
        try:
            return Product.objects.select_related(
                'category', 'seller', 'seller__seller_profile'
            ).prefetch_related('reviews', 'images').get(
                slug=slug, 
                available=True
            )
        except Product.DoesNotExist:
            return None
    
    @staticmethod
    def search_products(query: str, products: QuerySet[Product]) -> QuerySet[Product]:
        """
        Search products by name or description.
        
        Args:
            query: Search query string.
            products: Base queryset to filter.
            
        Returns:
            Filtered queryset.
        """
        if not query:
            return products
        return products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    @staticmethod
    def filter_products(
        products: QuerySet[Product],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        featured: Optional[bool] = None,
        in_stock: Optional[bool] = None
    ) -> QuerySet[Product]:
        """
        Apply filters to product queryset.
        
        Args:
            products: Base queryset.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            featured: Featured products only.
            in_stock: In stock products only.
            
        Returns:
            Filtered queryset.
        """
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        if featured:
            products = products.filter(featured=True)
        if in_stock:
            products = products.filter(stock__gt=0)
        return products
    
    @staticmethod
    def sort_products(products: QuerySet[Product], sort_by: str = 'name') -> QuerySet[Product]:
        """
        Sort products by specified field.
        
        Args:
            products: Queryset to sort.
            sort_by: Sort field (name, price, created, etc.).
            
        Returns:
            Sorted queryset.
        """
        valid_sorts = ['name', '-name', 'price', '-price', 'created', '-created']
        if sort_by in valid_sorts:
            return products.order_by(sort_by)
        return products.order_by('name')
    
    @staticmethod
    def paginate_products(products: QuerySet[Product], page: int = 1, per_page: int = 12) -> Tuple[Paginator, any]:
        """
        Paginate product queryset.
        
        Args:
            products: Queryset to paginate.
            page: Page number.
            per_page: Items per page.
            
        Returns:
            Tuple of (paginator, page_object).
        """
        paginator = Paginator(products, per_page)
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        return paginator, page_obj
    
    @staticmethod
    def get_related_products(product: Product, limit: int = 4) -> List[Product]:
        """
        Get related products from the same category.
        
        Args:
            product: Product to find related items for.
            limit: Maximum number of related products.
            
        Returns:
            List of related products.
        """
        cache_key = f'related_products_{product.category_id}_{product.id}'
        related = cache.get(cache_key)
        
        if related is None:
            related = list(Product.objects.filter(
                category=product.category,
                available=True,
                approved=True
            ).exclude(id=product.id).select_related('category', 'seller')[:limit])
            cache.set(cache_key, related, 60 * 30)  # Cache for 30 minutes
        
        return related
    
    @staticmethod
    def get_product_reviews_stats(product: Product) -> Dict[str, any]:
        """
        Get product review statistics.
        
        Args:
            product: Product instance.
            
        Returns:
            Dictionary with review statistics.
        """
        reviews = product.reviews.all() if hasattr(product, 'reviews') else []
        average_rating = 0
        if reviews:
            avg = reviews.aggregate(Avg('rating'))['rating__avg']
            average_rating = avg if avg else 0
        
        return {
            'average_rating': average_rating,
            'total_reviews': reviews.count(),
            'reviews': reviews
        }


class CategoryService:
    """Service for category-related business logic."""
    
    @staticmethod
    def get_all_categories() -> QuerySet[Category]:
        """
        Get all categories with caching.
        
        Returns:
            Cached queryset of all categories.
        """
        categories = cache.get('all_categories')
        if categories is None:
            categories = Category.objects.all()
            cache.set('all_categories', categories, 60 * 60)  # Cache for 1 hour
        return categories
    
    @staticmethod
    def get_category_by_slug(slug: str) -> Optional[Category]:
        """
        Get category by slug.
        
        Args:
            slug: Category slug.
            
        Returns:
            Category instance or None.
        """
        try:
            return Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            return None


class HomePageService:
    """Service for home page data aggregation."""
    
    @staticmethod
    def get_home_page_data() -> Dict[str, any]:
        """
        Get all data needed for home page with caching.
        
        Returns:
            Dictionary containing new arrivals, featured, best selling, and categories.
        """
        # New arrivals
        new_arrivals = cache.get('home_new_arrivals')
        if new_arrivals is None:
            new_arrivals = list(Product.objects.filter(
                major_category='new_arrivals',
                available=True,
                approved=True,
                seller__seller_profile__approval_status='approved'
            ).select_related('category', 'seller').order_by('-created')[:8])
            cache.set('home_new_arrivals', new_arrivals, 60 * 15)
        
        # Featured products
        featured_products = cache.get('home_featured_products')
        if featured_products is None:
            featured_products = list(Product.objects.filter(
                major_category='featured',
                available=True,
                approved=True,
                seller__seller_profile__approval_status='approved'
            ).select_related('category', 'seller').order_by('-created')[:8])
            cache.set('home_featured_products', featured_products, 60 * 15)
        
        # Best selling
        best_selling = cache.get('home_best_selling_products')
        if best_selling is None:
            best_selling = list(Product.objects.filter(
                major_category='best_selling',
                available=True,
                approved=True,
                seller__seller_profile__approval_status='approved'
            ).select_related('category', 'seller').order_by('-created')[:8])
            cache.set('home_best_selling_products', best_selling, 60 * 15)
        
        # Categories
        categories = cache.get('home_categories')
        if categories is None:
            categories = list(Category.objects.all()[:6])
            cache.set('home_categories', categories, 60 * 60)
        
        return {
            'new_arrivals': new_arrivals,
            'featured_products': featured_products,
            'best_selling_products': best_selling,
            'categories': categories,
        }

