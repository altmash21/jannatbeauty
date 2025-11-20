# ☁️ Cloudinary Integration Guide

## Overview

Cloudinary has been integrated into your Django e-commerce project. This provides:
- **Automatic image optimization** (WebP, compression)
- **CDN delivery** for faster loading
- **On-the-fly transformations** (resize, crop, etc.)
- **Free tier**: 25GB storage, 25GB bandwidth/month

## ✅ Installation Complete

The following packages have been added:
- `cloudinary>=1.36.0`
- `django-cloudinary-storage>=0.3.0`

## 🔧 Configuration

### Step 1: Create Cloudinary Account

1. Go to [https://cloudinary.com/users/register/free](https://cloudinary.com/users/register/free)
2. Sign up for a free account
3. After registration, you'll see your **Dashboard** with credentials

### Step 2: Get Your Cloudinary Credentials

From your Cloudinary Dashboard, copy:
- **Cloud Name** (e.g., `dxyz123456`)
- **API Key** (e.g., `123456789012345`)
- **API Secret** (e.g., `abcdefghijklmnopqrstuvwxyz123456`)

### Step 3: Add to Environment Variables

Add these to your `.env` file:

```env
# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

**⚠️ Important:** Never commit your `.env` file to version control!

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Run Migrations (if needed)

```bash
python manage.py migrate
```

## 🚀 How It Works

### Automatic Fallback

The system is configured to:
- **Use Cloudinary** if credentials are provided in `.env`
- **Fall back to local storage** if Cloudinary is not configured

This means:
- ✅ Works immediately in development (local storage)
- ✅ Easy to enable Cloudinary when ready
- ✅ No code changes needed to switch

### Current Setup

- **Models**: Using `ImageField` (works with both storage backends)
- **Storage**: Automatically uses Cloudinary when configured
- **URLs**: Images served from Cloudinary CDN when enabled

## 📸 Using Cloudinary Features

### In Templates (Optional)

You can use Cloudinary transformations in templates:

```html
<!-- Resize image to 300x300 -->
<img src="{{ product.image.url }}" alt="{{ product.name }}">

<!-- Or use Cloudinary transformations -->
{% load cloudinary %}
{% cloudinary product.image width=300 height=300 crop="fill" %}
```

### In Python Code

```python
from cloudinary import uploader

# Upload an image
result = uploader.upload("path/to/image.jpg")

# Transform an image URL
from cloudinary.utils import cloudinary_url
url, options = cloudinary_url("image_name", width=300, height=300, crop="fill")
```

## 🔄 Migrating Existing Images

If you have existing images in local storage:

### Option 1: Manual Upload (Recommended for small projects)

1. Go to Cloudinary Dashboard
2. Upload images manually
3. Update database with new URLs

### Option 2: Script Migration (For large projects)

Create a management command:

```python
# management/commands/migrate_to_cloudinary.py
from django.core.management.base import BaseCommand
from cloudinary import uploader
from store.models import Product

class Command(BaseCommand):
    def handle(self, *args, **options):
        for product in Product.objects.exclude(image=''):
            if product.image:
                result = uploader.upload(product.image.path)
                product.image = result['secure_url']
                product.save()
                self.stdout.write(f'Migrated {product.name}')
```

Run with:
```bash
python manage.py migrate_to_cloudinary
```

## 🎨 Image Transformations

Cloudinary supports automatic transformations via URL parameters:

### Common Transformations

```html
<!-- Resize to 500px width, maintain aspect ratio -->
<img src="{{ product.image.url }}?w_500">

<!-- Square thumbnail, 200x200 -->
<img src="{{ product.image.url }}?w_200,h_200,c_fill">

<!-- Auto format (WebP if supported) -->
<img src="{{ product.image.url }}?f_auto">

<!-- Quality optimization -->
<img src="{{ product.image.url }}?q_auto">

<!-- Combined: optimized, responsive -->
<img src="{{ product.image.url }}?f_auto,q_auto,w_500">
```

### Responsive Images

```html
<!-- Responsive image with srcset -->
<img src="{{ product.image.url }}?w_400"
     srcset="{{ product.image.url }}?w_400 400w,
             {{ product.image.url }}?w_800 800w,
             {{ product.image.url }}?w_1200 1200w"
     sizes="(max-width: 400px) 100vw, (max-width: 800px) 50vw, 33vw"
     alt="{{ product.name }}">
```

## 📊 Monitoring Usage

1. Log in to [Cloudinary Dashboard](https://cloudinary.com/console)
2. Check **Usage** tab for:
   - Storage used
   - Bandwidth consumed
   - Transformations performed

## 💰 Pricing

### Free Tier (Perfect for starting)
- 25GB storage
- 25GB bandwidth/month
- Unlimited transformations
- CDN delivery

### Paid Plans
- Start at $89/month for more storage/bandwidth
- Pay-as-you-go available

## 🔒 Security Best Practices

1. **Never expose API Secret** in frontend code
2. **Use signed URLs** for private images (if needed)
3. **Set up upload presets** for specific use cases
4. **Enable auto-format** for optimal delivery
5. **Use HTTPS** (already configured with `SECURE: True`)

## 🐛 Troubleshooting

### Images not uploading to Cloudinary

1. Check `.env` file has correct credentials
2. Verify credentials in Cloudinary Dashboard
3. Check `CLOUDINARY_AVAILABLE` in Django settings:
   ```python
   from django.conf import settings
   print(settings.CLOUDINARY_AVAILABLE)
   ```

### Images showing broken links

1. Ensure Cloudinary credentials are correct
2. Check if images exist in Cloudinary Dashboard
3. Verify `DEFAULT_FILE_STORAGE` setting

### Local storage still being used

- Check if Cloudinary credentials are set in `.env`
- Restart Django development server after adding credentials
- Verify `CLOUDINARY_AVAILABLE = True` in settings

## 📝 Environment Variables Reference

Add to `.env`:

```env
# Cloudinary (Optional - falls back to local if not set)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## 🎯 Next Steps

1. ✅ Create Cloudinary account
2. ✅ Add credentials to `.env`
3. ✅ Test image upload
4. ✅ Monitor usage in dashboard
5. ✅ Optimize images with transformations

## 📚 Resources

- [Cloudinary Documentation](https://cloudinary.com/documentation)
- [Django Cloudinary Storage Docs](https://github.com/klis87/django-cloudinary-storage)
- [Image Transformation Reference](https://cloudinary.com/documentation/image_transformations)

---

**Note:** The integration is backward compatible. Your existing code will work with or without Cloudinary configured.

