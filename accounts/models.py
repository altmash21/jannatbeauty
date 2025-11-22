from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import random
import string


class Profile(models.Model):
    USER_ROLES = [
        ('customer', 'Customer'),
        ('seller', 'Seller'),
        ('admin', 'Administrator'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='customer')
    phone = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zipcode = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='United States')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    @property
    def is_seller(self):
        return self.role == 'seller'
    
    @property
    def is_customer(self):
        return self.role == 'customer'
    
    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def full_address(self):
        address_parts = [self.address, self.city, self.state, self.zipcode]
        return ', '.join([part for part in address_parts if part])


class SellerProfile(models.Model):
    APPROVAL_STATUS = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=200)
    business_description = models.TextField()
    business_address = models.CharField(max_length=255)
    business_phone = models.CharField(max_length=20)
    business_email = models.EmailField()
    tax_id = models.CharField(max_length=50, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # Percentage
    allowed_major_categories = models.JSONField(
        default=list,
        blank=True,
        help_text='List of major categories this seller can manage (e.g., ["new_arrivals", "featured", "best_selling"]). Empty list means all categories.'
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.business_name} - {self.get_approval_status_display()}"
    
    @property
    def is_approved(self):
        return self.approval_status == 'approved'
    
    @property
    def can_sell(self):
        return self.approval_status == 'approved'
    
    def can_manage_major_category(self, category):
        """Check if seller can manage a specific major category"""
        # Only allow if admin has explicitly granted permission (non-empty list)
        if not self.allowed_major_categories or len(self.allowed_major_categories) == 0:
            return False
        return category in self.allowed_major_categories
    
    def get_manageable_major_categories(self):
        """Get list of major categories seller can manage"""
        # Only return categories if admin has explicitly granted permission
        if not self.allowed_major_categories or len(self.allowed_major_categories) == 0:
            return []  # No categories if not explicitly allowed by admin
        
        from store.models import Product
        all_categories = [choice[0] for choice in Product.MAJOR_CATEGORY_CHOICES]
        return [cat for cat in all_categories if cat in self.allowed_major_categories]


# Signal to create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=Profile)
def create_seller_profile(sender, instance, **kwargs):
    if instance.role == 'seller':
        # Only create SellerProfile if it doesn't exist and user doesn't have one
        # This prevents duplicate creation during registration
        if not SellerProfile.objects.filter(user=instance.user).exists():
            # Create minimal SellerProfile for users who somehow got seller role without one
            # This is a fallback - normally SellerProfile is created during registration
            SellerProfile.objects.create(
                user=instance.user,
                business_name=f"{instance.user.username}'s Business",
                business_description="Please update your business information",
                business_address="Please update your business address",
                business_phone="Please update your phone",
                business_email=instance.user.email
            )


class Notification(models.Model):
    """Customer notifications for order updates, promotions, and system messages"""
    NOTIFICATION_TYPES = [
        ('order', 'Order Update'),
        ('product', 'Product Update'),
        ('promotion', 'Promotion'),
        ('system', 'System Message'),
        ('account', 'Account Update'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, help_text="Optional link to related page")
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    @property
    def icon(self):
        """Return icon class based on notification type"""
        icons = {
            'order': 'fas fa-shopping-bag',
            'product': 'fas fa-box',
            'promotion': 'fas fa-tag',
            'system': 'fas fa-info-circle',
            'account': 'fas fa-user',
        }
        return icons.get(self.notification_type, 'fas fa-bell')


class PasswordResetOTP(models.Model):
    """Model to handle password reset via email OTP"""
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_otps')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.email} - {self.otp_code}"

    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        return not self.is_used and timezone.now() < self.expires_at

    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at

    @classmethod
    def generate_otp(cls, user):
        """Generate a new OTP for the user"""
        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Set expiry time (10 minutes from now)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        # Create new OTP
        otp_instance = cls.objects.create(
            email=user.email,
            otp_code=otp_code,
            expires_at=expires_at,
            user=user
        )
        
        return otp_instance

    def mark_as_used(self):
        """Mark the OTP as used"""
        self.is_used = True
        self.save()


class RegistrationOTP(models.Model):
    """Model to handle account registration via email OTP"""
    email = models.EmailField()
    password = models.CharField(max_length=128)  # Store hashed password temporarily
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Registration OTP for {self.email} - {self.otp_code}"

    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        return not self.is_used and timezone.now() < self.expires_at

    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at

    @classmethod
    def generate_otp(cls, email, password):
        """Generate a new OTP for registration"""
        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Set expiry time (10 minutes from now)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        # Create new OTP
        otp_instance = cls.objects.create(
            email=email,
            password=password,  # Store password temporarily (will be hashed when creating user)
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        return otp_instance

    def mark_as_used(self):
        """Mark the OTP as used"""
        self.is_used = True
        self.save()
