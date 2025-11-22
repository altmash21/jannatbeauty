from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from PIL import Image
import uuid
import os
from io import BytesIO
from django.core.files.base import ContentFile


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_list_by_category', args=[self.slug])


class SubCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='subcategories/', blank=True, null=True)
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Subcategories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_list_by_subcategory', args=[self.slug])


class Product(models.Model):
    seller = models.ForeignKey(User, related_name='products', on_delete=models.CASCADE, default=1)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    MAJOR_CATEGORY_CHOICES = [
        ('new_arrivals', 'New Arrivals'),
        ('featured', 'Featured'),
        ('best_selling', 'Best Selling'),
        ('none', 'None'),
    ]
    major_category = models.CharField(max_length=20, choices=MAJOR_CATEGORY_CHOICES, default='new_arrivals', blank=True)
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True, blank=True, db_index=True, help_text='Stock Keeping Unit - Leave blank to auto-generate')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)  # Products need approval before being visible
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['sku']),
            models.Index(fields=['created']),
            models.Index(fields=['seller', 'approved']),
        ]
        permissions = [
            ("can_add_product", "Can add product"),
            ("can_approve_product", "Can approve product"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Resize image to fixed dimensions if image is provided
        # Check if image has been changed (new upload or update)
        if self.image and hasattr(self.image, 'file'):
            # Fixed dimensions for product images (square format)
            IMAGE_WIDTH = 500
            IMAGE_HEIGHT = 500
            
            try:
                # Open the image
                img = Image.open(self.image)
                
                # Convert RGBA to RGB if necessary (for PNGs with transparency)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                
                # Resize and crop to fixed dimensions (maintain aspect ratio, center crop)
                img.thumbnail((IMAGE_WIDTH, IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                
                # Create a new image with fixed dimensions and paste the resized image centered
                new_img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), (255, 255, 255))
                img_width, img_height = img.size
                paste_x = (IMAGE_WIDTH - img_width) // 2
                paste_y = (IMAGE_HEIGHT - img_height) // 2
                new_img.paste(img, (paste_x, paste_y))
                
                # Save the resized image
                output = BytesIO()
                new_img.save(output, format='JPEG', quality=95, optimize=True)
                output.seek(0)
                
                # Update the image field
                filename = os.path.basename(self.image.name) if self.image.name else f"product_{self.pk or 'new'}.jpg"
                name, ext = os.path.splitext(filename)
                if not name:
                    name = f"product_{self.pk or 'new'}"
                self.image.save(f"{name}.jpg", ContentFile(output.read()), save=False)
                img.close()
            except Exception as e:
                # If image processing fails, log the error but continue saving
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error processing image for product {self.name}: {str(e)}")
                # Continue with original image if processing fails
        
        # Save first to get an ID for SKU generation (if new product)
        super().save(*args, **kwargs)
        
        # Auto-generate SKU if not provided
        if not self.sku:
            # Generate SKU in format: PROD-00001
            self.sku = f"PROD-{self.pk:05d}"
            # Save again with just the SKU field
            super().save(update_fields=['sku'])

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    @property
    def is_on_sale(self):
        return self.compare_price and self.compare_price > self.price

    @property
    def discount_percentage(self):
        if self.is_on_sale:
            discount = ((self.compare_price - self.price) / self.compare_price) * 100
            return round(discount)
        return 0

    @property
    def seller_name(self):
        """Get the seller's business name or username"""
        if hasattr(self.seller, 'seller_profile'):
            return self.seller.seller_profile.business_name
        return self.seller.username

    @property
    def is_approved_seller(self):
        """Check if the seller is approved"""
        if hasattr(self.seller, 'seller_profile'):
            return self.seller.seller_profile.is_approved
        return False

    def can_be_purchased(self):
        """Check if product can be purchased"""
        return (self.available and 
                self.approved and 
                self.stock > 0 and 
                self.is_approved_seller)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = f"Image of {self.product.name}"
        
        # Resize image to fixed dimensions if image is provided
        # Check if image has been changed (new upload or update)
        if self.image and hasattr(self.image, 'file'):
            # Fixed dimensions for product images (square format)
            IMAGE_WIDTH = 500
            IMAGE_HEIGHT = 500
            
            try:
                # Open the image
                img = Image.open(self.image)
                
                # Convert RGBA to RGB if necessary (for PNGs with transparency)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                
                # Resize and crop to fixed dimensions (maintain aspect ratio, center crop)
                img.thumbnail((IMAGE_WIDTH, IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                
                # Create a new image with fixed dimensions and paste the resized image centered
                new_img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), (255, 255, 255))
                img_width, img_height = img.size
                paste_x = (IMAGE_WIDTH - img_width) // 2
                paste_y = (IMAGE_HEIGHT - img_height) // 2
                new_img.paste(img, (paste_x, paste_y))
                
                # Save the resized image
                output = BytesIO()
                new_img.save(output, format='JPEG', quality=95, optimize=True)
                output.seek(0)
                
                # Update the image field
                filename = os.path.basename(self.image.name) if self.image.name else f"product_image_{self.pk or 'new'}.jpg"
                name, ext = os.path.splitext(filename)
                if not name:
                    name = f"product_image_{self.pk or 'new'}"
                self.image.save(f"{name}.jpg", ContentFile(output.read()), save=False)
                img.close()
            except Exception as e:
                # If image processing fails, log the error but continue saving
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error processing image for ProductImage: {str(e)}")
                # Continue with original image if processing fails
        
        super().save(*args, **kwargs)


class Lead(models.Model):
    """Model to store lead information from discount popup"""
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    coupon_code = models.CharField(max_length=50, blank=True, null=True, help_text='Coupon code generated for this lead')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    email_sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
    
    def __str__(self):
        return f"{self.name} - {self.mobile} ({self.coupon_code or 'No coupon'})"


