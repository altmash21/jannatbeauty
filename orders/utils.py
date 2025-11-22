"""Utility functions for order-related email notifications"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order, OrderItem


def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        recipient_email = order.email
        
        # Prepare email content
        subject = f'Order Confirmation - #{order.order_number or order.id}'
        
        # Build order items list
        items_list = []
        for item in order.items.all():
            items_list.append({
                'name': item.product.name,
                'quantity': item.quantity,
                'price': item.price,
                'total': item.get_cost()
            })
        
        message = f'''Hello {order.first_name},

Thank you for your order! Your order has been confirmed and is being processed.

Order Details:
- Order Number: {order.order_number or order.id}
- Order Date: {order.created.strftime("%B %d, %Y at %I:%M %p")}
- Payment Method: {order.get_payment_method_display()}
- Total Amount: ₹{order.total_amount}

Order Items:
'''
        for item in items_list:
            message += f'- {item["name"]} x {item["quantity"]} = ₹{item["total"]}\n'
        
        message += f'''
Shipping Address:
{order.full_address}

You can track your order status from your dashboard.

Thank you for shopping with Jannat Library!

Best regards,
Jannat Library Team
'''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to send order confirmation email for order {order.id}: {str(e)}')


def send_order_status_update_email(order):
    """Send order status update email to customer"""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        recipient_email = order.email
        
        status_messages = {
            'processing': 'Your order is now being processed.',
            'shipped': 'Great news! Your order has been shipped.',
            'delivered': 'Your order has been delivered. Enjoy your purchase!',
            'cancelled': 'Your order has been cancelled.',
        }
        
        status_display = {
            'processing': 'Processing',
            'shipped': 'Shipped',
            'delivered': 'Delivered',
            'cancelled': 'Cancelled',
        }
        
        if order.order_status not in status_messages:
            return
        
        subject = f'Order Update - #{order.order_number or order.id}'
        
        message = f'''Hello {order.first_name},

Your order status has been updated.

Order Number: {order.order_number or order.id}
New Status: {status_display.get(order.order_status, order.order_status.title())}

{status_messages[order.order_status]}

'''
        
        if order.order_status == 'shipped' and order.awb_code:
            message += f'Tracking Number: {order.awb_code}\n'
            if order.courier_name:
                message += f'Courier: {order.courier_name}\n'
        
        message += f'''
You can track your order from your dashboard.

Thank you for shopping with Jannat Library!

Best regards,
Jannat Library Team
'''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to send order status update email for order {order.id}: {str(e)}')


def send_new_order_notification_to_seller(order):
    """Send new order notification email to seller(s) whose products are in the order"""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        
        # Group order items by seller
        seller_items = {}
        for item in order.items.all():
            seller = item.product.seller
            if seller not in seller_items:
                seller_items[seller] = []
            seller_items[seller].append(item)
        
        # Send email to each seller
        for seller, items in seller_items.items():
            try:
                seller_email = seller.email
                if not seller_email:
                    continue
                
                subject = f'New Order - #{order.order_number or order.id}'
                
                # Build items list for this seller
                items_list = []
                seller_total = 0
                for item in items:
                    item_total = item.get_cost()
                    seller_total += item_total
                    items_list.append({
                        'name': item.product.name,
                        'quantity': item.quantity,
                        'price': item.price,
                        'total': item_total
                    })
                
                message = f'''Hello {seller.get_full_name() or seller.username},

You have received a new order containing your products!

Order Details:
- Order Number: {order.order_number or order.id}
- Order Date: {order.created.strftime("%B %d, %Y at %I:%M %p")}
- Customer: {order.full_name}
- Customer Email: {order.email}
- Payment Method: {order.get_payment_method_display()}
- Total Amount (Your Products): ₹{seller_total}

Your Products in This Order:
'''
                for item in items_list:
                    message += f'- {item["name"]} x {item["quantity"]} = ₹{item["total"]}\n'
                
                message += f'''
Shipping Address:
{order.full_address}

Please log in to your seller dashboard to process this order.

Thank you!
Jannat Library Team
'''
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[seller_email],
                    fail_silently=False,
                )
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send order notification email to seller {seller.id}: {str(e)}')
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to send new order notification emails for order {order.id}: {str(e)}')


def send_order_notification_to_admin(order):
    """Send new order notification email to admin"""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        
        # Get admin email
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if not admin_email and hasattr(settings, 'ADMINS') and settings.ADMINS:
            admin_email = settings.ADMINS[0][1]  # First admin's email
        
        if not admin_email:
            admin_email = from_email  # Fallback to from_email
        
        subject = f'New Order Received - #{order.order_number or order.id}'
        
        # Build order items list
        items_list = []
        for item in order.items.all():
            items_list.append({
                'name': item.product.name,
                'seller': item.product.seller.get_full_name() or item.product.seller.username,
                'quantity': item.quantity,
                'price': item.price,
                'total': item.get_cost()
            })
        
        message = f'''New Order Received

Order Details:
- Order Number: {order.order_number or order.id}
- Order Date: {order.created.strftime("%B %d, %Y at %I:%M %p")}
- Customer: {order.full_name}
- Customer Email: {order.email}
- Payment Method: {order.get_payment_method_display()}
- Total Amount: ₹{order.total_amount}

Order Items:
'''
        for item in items_list:
            message += f'- {item["name"]} (Seller: {item["seller"]}) x {item["quantity"]} = ₹{item["total"]}\n'
        
        message += f'''
Shipping Address:
{order.full_address}

Please check the admin dashboard for order management.

Jannat Library System
'''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to send order notification email to admin for order {order.id}: {str(e)}')

