# Redis Integration Guide for E-commerce Project

## Installation Steps

### 1. Install Redis Server

**Windows:**
- Download from: https://github.com/microsoftarchive/redis/releases
- Or use WSL: `sudo apt-get install redis-server`
- Or use Docker: `docker run -d -p 6379:6379 redis:latest`

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# Mac (using Homebrew)
brew install redis

# Start Redis
redis-server
```

### 2. Install Python Packages

Add to `requirements.txt`:
```
django-redis>=5.4.0
redis>=5.0.0
```

Then install:
```bash
pip install django-redis redis
```

### 3. Configure Django Settings

Add to `ecommerce/settings.py`:

```python
# Redis Configuration
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default=6379)
REDIS_DB = config('REDIS_DB', default=0)

# Cache Configuration (using Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,  # Don't break if Redis is down
        },
        'KEY_PREFIX': 'ecommerce',
        'TIMEOUT': 300,  # 5 minutes default timeout
    }
}

# Session Configuration (optional - use Redis for sessions)
# Uncomment to use Redis for sessions instead of database
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_CACHE_ALIAS = 'default'

# Or use Redis directly for sessions
# SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'  # Hybrid: cache + DB fallback
```

### 4. Usage Examples

#### Caching Product Listings

In `store/views.py`:
```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def product_list(request, category_slug=None):
    # Your existing code
    pass

# Or manual caching:
def product_list(request, category_slug=None):
    cache_key = f'products_{category_slug or "all"}'
    products = cache.get(cache_key)
    
    if products is None:
        products = Product.objects.filter(available=True)
        cache.set(cache_key, products, 60 * 15)  # 15 minutes
    
    return render(request, 'store/product/list.html', {'products': products})
```

#### Caching Cart Count

In `cart/context_processors.py`:
```python
from django.core.cache import cache

def cart(request):
    if request.user.is_authenticated:
        cache_key = f'cart_count_{request.user.id}'
        cart_count = cache.get(cache_key)
        if cart_count is None:
            cart_obj = Cart(request)
            cart_count = len(cart_obj)
            cache.set(cache_key, cart_count, 60 * 5)  # 5 minutes
    else:
        cart_obj = Cart(request)
        cart_count = len(cart_obj)
    
    return {'cart_count': cart_count}
```

#### Rate Limiting (for API endpoints)

```python
from django.core.cache import cache
from django.http import JsonResponse

def api_endpoint(request):
    ip = request.META.get('REMOTE_ADDR')
    cache_key = f'rate_limit_{ip}'
    requests = cache.get(cache_key, 0)
    
    if requests >= 100:  # 100 requests per hour
        return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
    
    cache.set(cache_key, requests + 1, 3600)  # 1 hour
    # Your API logic here
```

## Benefits for Your E-commerce Site

1. **Faster Page Loads**: Cache product listings, categories
2. **Better Session Performance**: Redis sessions are much faster than DB sessions
3. **Scalability**: Handle more concurrent users
4. **Real-time Features**: Can add live inventory updates, notifications
5. **Search Results Caching**: Cache search queries

## Migration Strategy

1. **Phase 1**: Install Redis, configure caching (non-breaking)
2. **Phase 2**: Start caching product listings and categories
3. **Phase 3**: (Optional) Move sessions to Redis
4. **Phase 4**: Add rate limiting and advanced features

## Testing Redis Connection

```python
# In Django shell: python manage.py shell
from django.core.cache import cache

# Test connection
cache.set('test_key', 'test_value', 30)
print(cache.get('test_key'))  # Should print: test_value
```

## Production Considerations

- Use Redis password authentication
- Configure Redis persistence (RDB or AOF)
- Set up Redis monitoring
- Use Redis Sentinel for high availability
- Consider Redis Cloud for managed hosting

