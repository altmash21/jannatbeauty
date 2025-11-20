from django.core.cache import cache
from .models import Category


def categories(request):
    """Make all categories available in all templates"""
    categories_list = cache.get('all_categories_list')
    if categories_list is None:
        categories_list = list(Category.objects.all().order_by('name'))
        cache.set('all_categories_list', categories_list, 60 * 60)  # Cache for 1 hour
    return {
        'all_categories': categories_list,
    }

