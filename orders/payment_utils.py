"""
Updated payment flow that creates orders only after successful payment
"""

def create_order_from_session(order_id, session_data):
    """Create an order from session data after successful payment"""
    import logging
    from django.contrib.auth.models import User
    from .models import Order, OrderItem
    from store.models import Product
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get user if authenticated
        user = None
        if session_data.get('user_id'):
            try:
                user = User.objects.get(id=session_data['user_id'])
            except User.DoesNotExist:
                pass
        
        # Create the actual order
        order = Order.objects.create(
            id=order_id,  # Use the same ID as temp order
            user=user,
            first_name=session_data['first_name'],
            last_name=session_data['last_name'],
            email=session_data['email'],
            address_line1=session_data['address'],
            address_line2=session_data.get('address2', ''),
            city=session_data['city'],
            state=session_data['state'],
            postal_code=session_data['zipcode'],
            country=session_data['country'],
            phone=session_data['phone'],
            payment_method=session_data['payment_method'],
            total_amount=session_data['total_amount'],
            paid=True  # Mark as paid since payment is successful
        )
        
        # Create order items and update stock
        for item_data in session_data['cart_items']:
            try:
                product = Product.objects.get(id=item_data['product_id'])
                quantity = item_data['quantity']
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item_data['price'],
                    quantity=quantity
                )
                
                # Update stock
                product.stock -= quantity
                product.save(update_fields=['stock'])
                
            except Product.DoesNotExist:
                logger.warning(f'Product {item_data["product_id"]} not found during order creation')
                continue
        
        logger.info(f'Order {order_id} created successfully from session data')
        return order
        
    except Exception as e:
        logger.error(f'Error creating order from session: {str(e)}')
        raise