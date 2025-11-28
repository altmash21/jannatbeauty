from django.db import models
from django.contrib.auth.models import User
from store.models import Product
from django.core.validators import MinValueValidator
import uuid


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, blank=True, null=True, help_text='Human-readable order number')
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=[('cashfree', 'Cashfree'), ('cod', 'Cash on Delivery')], default='cod', help_text='Payment method used for this order')
    payment_id = models.CharField(max_length=100, blank=True, null=True, help_text='Payment gateway order/transaction ID')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    
    # Shiprocket fields
    shiprocket_order_id = models.CharField(max_length=100, blank=True, null=True)
    shiprocket_shipment_id = models.CharField(max_length=100, blank=True, null=True)
    awb_code = models.CharField(max_length=100, blank=True, null=True, help_text='Air Waybill tracking number')
    courier_name = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'Order {self.order_number or self.id}'
    def save(self, *args, **kwargs):
        # Auto-generate order_number if not set
        if not self.order_number:
            from django.utils import timezone
            today = timezone.localdate()
            prefix = 'JB'
            date_str = today.strftime('%Y%m%d')
            # Count orders for today to get sequence
            from django.db.models import Count
            daily_count = Order.objects.filter(created__date=today).count() + 1
            self.order_number = f'{prefix}{date_str}{daily_count:03d}'
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_address(self):
        return f'{self.address}, {self.city}, {self.state} {self.zipcode}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField(default=1)
    # Track per-item fulfillment status for seller updates
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    def get_cost(self):
        return self.price * self.quantity
