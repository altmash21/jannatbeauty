"""Utility functions for order-related email notifications"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order, OrderItem


def send_order_confirmation_email(order):
    """Send order confirmation email to customer using HTML template"""
    try:
        from django.template.loader import render_to_string
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        recipient_email = order.email
        
        # Prepare email content
        subject = f'Order Confirmation #{order.order_number or order.id} - JannatLibrary.com'
        
        # Build order items list for template
        order_items = []
        for item in order.items.all():
            order_items.append({
                'name': item.product.name,
                'quantity': item.quantity,
                'price': item.price,
                'total': item.get_cost()
            })
        
        # Render HTML template
        html_message = render_to_string('emails/order_confirmation.html', {
            'order': order,
            'order_items': order_items,
        })
        
        # Plain text fallback
        plain_message = f'''Hello {order.first_name},

Thank you for your order! Your order has been confirmed and is being processed.

Order Details:
- Order Number: {order.order_number or order.id}
- Order Date: {order.created.strftime("%B %d, %Y at %I:%M %p")}
- Payment Method: {order.get_payment_method_display()}
- Total Amount: ₹{order.total_amount}

Order Items:
'''
        for item in order_items:
            plain_message += f'- {item["name"]} x {item["quantity"]} = ₹{item["total"]}\n'
        
        plain_message += f'''
Shipping Address:
{order.first_name} {order.last_name}
{order.address}
{order.city}, {order.state} {order.zipcode}

You can track your order at: https://jannatlibrary.com/orders/{order.id}/

Thank you for shopping with JannatLibrary.com!

Best regards,
Jannat Library Team
JannatLibrary.com
'''
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to send order confirmation email for order {order.id}: {str(e)}')


def send_order_status_update_email(order):
    """Send order status update email to customer using HTML template"""
    try:
        from django.template.loader import render_to_string
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        recipient_email = order.email
        
        status_messages = {
            'processing': 'Your order is now being processed and will be shipped soon.',
            'shipped': 'Great news! Your order has been shipped and is on its way to you.',
            'delivered': 'Your order has been delivered successfully. Enjoy your purchase!',
            'cancelled': 'Your order has been cancelled. If this was unexpected, please contact our support team.',
        }
        
        status_display = {
            'processing': 'Processing',
            'shipped': 'Shipped',
            'delivered': 'Delivered',
            'cancelled': 'Cancelled',
        }
        
        if order.order_status not in status_messages:
            return
        
        subject = f'Order Update #{order.order_number or order.id} - JannatLibrary.com'
        
        # Render HTML template
        html_message = render_to_string('emails/order_status_update.html', {
            'order': order,
            'status_message': status_messages[order.order_status],
            'status_display': status_display.get(order.order_status, order.order_status.title()),
        })
        
        # Plain text fallback
        plain_message = f'''Hello {order.first_name},

Your order status has been updated.

Order Number: {order.order_number or order.id}
New Status: {status_display.get(order.order_status, order.order_status.title())}

{status_messages[order.order_status]}

'''
        
        if order.order_status == 'shipped' and order.awb_code:
            plain_message += f'Tracking Information:\nAWB/Tracking Number: {order.awb_code}\n'
            if order.courier_name:
                plain_message += f'Courier: {order.courier_name}\n'
        
        plain_message += f'''
You can track your order at: https://jannatlibrary.com/orders/{order.id}/

Best regards,
Jannat Library Team
JannatLibrary.com
'''
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_message,
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

