# Redis Setup - Quick Start Guide

## ✅ Redis Integration Complete!

Redis has been successfully integrated into your Django e-commerce project. Here's what was done:

### What Was Integrated:

1. **Requirements Updated** (`requirements.txt`)
   - Added `django-redis>=5.4.0`
   - Added `redis>=5.0.0`

2. **Settings Configured** (`ecommerce/settings.py`)
   - Automatic Redis detection with fallback to local memory cache
   - Graceful degradation if Redis is unavailable
   - Configurable via environment variables

3. **Caching Implemented**:
   - **Product Listings**: Cached for 15 minutes (when no filters/search)
   - **Product Details**: Cached for 30 minutes
   - **Home Page**: New arrivals, featured, and best-selling products cached for 15 minutes
   - **Categories**: Cached for 1 hour

4. **Cache Invalidation**:
   - Automatic cache clearing when products are created/updated/deleted
   - Category cache invalidation on changes
   - Smart pattern-based deletion for related products

## 🚀 Installation Steps

### Step 1: Install Python Packages
```bash
pip install -r requirements.txt
```

### Step 2: Install Redis Server

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

### Step 3: Verify Redis is Running
```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

### Step 4: (Optional) Configure Environment Variables
Create a `.env` file in your project root:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Leave empty if no password
```

## 🧪 Testing Redis Connection

### Method 1: Django Shell
```bash
python manage.py shell
```

```python
from django.core.cache import cache

# Test connection
cache.set('test_key', 'test_value', 30)
print(cache.get('test_key'))  # Should print: test_value

# Check if Redis is being used
from django.conf import settings
print(f"Redis Available: {settings.REDIS_AVAILABLE}")
```

### Method 2: Check Django Startup
When you run `python manage.py runserver`, check the console output. If Redis is available, it will use Redis. If not, it will automatically fall back to local memory cache (no errors).

## 📊 What Gets Cached

| Item | Cache Duration | Cache Key |
|------|---------------|-----------|
| Product List (no filters) | 15 minutes | `product_list_*` |
| Product Detail | 30 minutes | `product_detail_{slug}` |
| Related Products | 30 minutes | `related_products_{category_id}_{product_id}` |
| Home - New Arrivals | 15 minutes | `home_new_arrivals` |
| Home - Featured | 15 minutes | `home_featured_products` |
| Home - Best Selling | 15 minutes | `home_best_selling_products` |
| Categories | 1 hour | `all_categories`, `home_categories` |

## 🔄 Cache Invalidation

Cache is automatically invalidated when:
- Products are created, updated, or deleted
- Categories are created or updated
- Product approval status changes

## ⚙️ Configuration Options

### Use Redis for Sessions (Optional)
Uncomment these lines in `ecommerce/settings.py`:
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### Adjust Cache Timeouts
Edit cache timeout values in `store/views.py`:
- Product list: `60 * 15` (15 minutes)
- Product detail: `60 * 30` (30 minutes)
- Home page: `60 * 15` (15 minutes)
- Categories: `60 * 60` (1 hour)

## 🎯 Benefits

1. **Faster Page Loads**: Product listings load from cache instead of database
2. **Reduced Database Load**: Fewer queries to SQLite/PostgreSQL
3. **Better Scalability**: Can handle more concurrent users
4. **Graceful Fallback**: Works even if Redis is unavailable (uses local memory cache)

## 🐛 Troubleshooting

### Redis Not Connecting?
- Check if Redis server is running: `redis-cli ping`
- Verify host/port in settings
- Check firewall settings
- The app will automatically fall back to local memory cache

### Cache Not Updating?
- Cache is automatically invalidated on product/category changes
- You can manually clear cache:
  ```python
  from django.core.cache import cache
  cache.clear()  # Clear all cache
  ```

### Performance Not Improved?
- Make sure Redis is actually running
- Check `settings.REDIS_AVAILABLE` in Django shell
- Verify cache keys are being set: `redis-cli keys "ecommerce:*"`

## 📝 Next Steps (Optional Enhancements)

1. **Session Storage**: Move sessions to Redis for better performance
2. **Rate Limiting**: Use Redis for API rate limiting
3. **Real-time Features**: Use Redis pub/sub for live updates
4. **Search Caching**: Cache search results
5. **Cart Caching**: Cache cart counts for authenticated users

## 🔒 Production Considerations

- Set up Redis password authentication
- Configure Redis persistence (RDB or AOF)
- Use Redis Sentinel for high availability
- Monitor Redis memory usage
- Consider Redis Cloud for managed hosting

---

**Note**: The integration is production-ready and will work with or without Redis. If Redis is unavailable, the app automatically uses local memory cache.

