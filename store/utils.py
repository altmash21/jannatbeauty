"""Utility functions for store-related email notifications"""
from django.core.mail import send_mail
from django.conf import settings
from .models import Product


def send_product_approval_email(product, approved):
    """Send email to seller when their product is approved or rejected"""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        seller = product.seller
        
        if not seller or not hasattr(seller, 'email'):
            return
        
        recipient_email = seller.email
        if not recipient_email:
            # Try seller profile business email
            if hasattr(seller, 'seller_profile'):
                recipient_email = seller.seller_profile.business_email
            if not recipient_email:
                return
        
        if approved:
            subject = f'Product Approved - {product.name}'
            message = f'''Hello {seller.get_full_name() or seller.username},

Great news! Your product has been approved and is now live on Jannat Library.

Product Details:
- Product Name: {product.name}
- SKU: {product.sku}
- Price: ₹{product.price}
- Stock: {product.stock}

Your product is now visible to customers and ready for purchase.

You can view and manage your products from your seller dashboard.

Thank you for selling with Jannat Library!

Best regards,
Jannat Library Team
'''
        else:
            subject = f'Product Disapproved - {product.name}'
            message = f'''Hello {seller.get_full_name() or seller.username},

We regret to inform you that your product has been disapproved.

Product Details:
- Product Name: {product.name}
- SKU: {product.sku}

Your product will not be visible to customers. Please review your product details and ensure they meet our guidelines.

You can edit your product from your seller dashboard and resubmit for approval.

If you have any questions, please contact us at {from_email}

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
        logger.error(f'Failed to send product approval email for product {product.id}: {str(e)}')


def send_review_notification_email(review):
    """Send email to seller when a review is posted on their product"""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@jannatlibrary.com')
        product = review.product
        seller = product.seller
        
        if not seller or not hasattr(seller, 'email'):
            return
        
        recipient_email = seller.email
        if not recipient_email:
            # Try seller profile business email
            if hasattr(seller, 'seller_profile'):
                recipient_email = seller.seller_profile.business_email
            if not recipient_email:
                return
        
        subject = f'New Review - {product.name}'
        
        stars = '⭐' * review.rating
        verified_text = ' (Verified Purchase)' if review.verified_purchase else ''
        
        message = f'''Hello {seller.get_full_name() or seller.username},

You have received a new review on your product!

Product: {product.name}
Customer: {review.user.get_full_name() or review.user.username}{verified_text}
Rating: {stars} ({review.rating}/5)

Review Title: {review.title}

Review:
{review.comment}

View this review on your product page or seller dashboard.

Thank you for selling with Jannat Library!

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
        logger.error(f'Failed to send review notification email for review {review.id}: {str(e)}')

