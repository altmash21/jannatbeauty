from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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
