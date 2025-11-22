from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from store.models import Product
from orders.models import Order, OrderItem

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user has purchased this product
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
        order__order_status='delivered'
    ).exists()
    
    if request.method == 'POST':
        # Check if user already reviewed this product
        if Review.objects.filter(product=product, user=request.user).exists():
            messages.error(request, 'You have already reviewed this product.')
            return redirect('store:product_detail', slug=product.slug)
        
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        
        if not all([rating, title, comment]):
            messages.error(request, 'Please fill in all fields.')
            return redirect('store:product_detail', slug=product.slug)
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            messages.error(request, 'Invalid rating value.')
            return redirect('store:product_detail', slug=product.slug)
        
        review = Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            title=title,
            comment=comment,
            verified_purchase=has_purchased
        )
        
        # Send review notification email to seller
        try:
            from store.utils import send_review_notification_email
            send_review_notification_email(review)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send review notification email: {str(e)}')
        
        messages.success(request, 'Thank you for your review!')
        return redirect('store:product_detail', slug=product.slug)
    
    return redirect('store:product_detail', slug=product.slug)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product_slug = review.product.slug
    review.delete()
    messages.success(request, 'Review deleted successfully.')
    return redirect('store:product_detail', slug=product_slug)
