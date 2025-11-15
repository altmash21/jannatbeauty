from decimal import Decimal
from django.conf import settings
from store.models import Product
import logging


logger = logging.getLogger(__name__)


class Cart:
    def serialize(self):
        """
        Return a serializable version of the cart for storing in session or sending to APIs.
        """
        cleaned_cart = {}
        for product_id, item in self.cart.items():
            cleaned_cart[product_id] = {
                'quantity': item['quantity'],
                'price': str(item['price'])
            }
        return cleaned_cart
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        logger.debug(f"Adding product to cart: {product_id}, quantity: {quantity}, override: {override_quantity}")

        # Check if product is available and has sufficient stock
        if not product.available:
            logger.error(f"Product '{product.name}' is not available")
            raise ValueError(f"Product '{product.name}' is not available")

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }

        if override_quantity:
            new_quantity = quantity
        else:
            new_quantity = self.cart[product_id]['quantity'] + quantity

        # Check stock availability (only if stock tracking is enabled)
        if product.stock > 0 and new_quantity > product.stock:
            logger.error(f"Insufficient stock for '{product.name}'. Requested: {new_quantity}, Available: {product.stock}")
            raise ValueError(f"Insufficient stock. Only {product.stock} items available for '{product.name}'")

        self.cart[product_id]['quantity'] = new_quantity
        logger.debug(f"Product '{product.name}' added to cart. New quantity: {new_quantity}")
        self.save()

    def save(self):
        """
        Mark the session as "modified" to make sure it gets saved
        Remove any non-serializable objects before saving.
        """
        logger.debug("Saving cart to session")
        # Clean the cart data before saving to session
        cleaned_cart = {}
        for product_id, item in self.cart.items():
            # Only keep serializable data
            cleaned_cart[product_id] = {
                'quantity': item['quantity'],
                'price': str(item['price'])
            }
        
        self.session[settings.CART_SESSION_ID] = cleaned_cart
        self.cart = cleaned_cart  # Update local reference
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products
        from the database. Handles cases where products might have been deleted.
        """
        product_ids = list(self.cart.keys())
        
        # Get all products that exist in the database
        products = Product.objects.filter(id__in=product_ids)
        products_dict = {str(p.id): p for p in products}
        
        # Track if we need to clean up deleted products
        deleted_product_ids = []
        
        # Yield valid cart items
        for product_id, item in self.cart.items():
            product = products_dict.get(product_id)
            
            if product is None:
                # Product was deleted from database
                deleted_product_ids.append(product_id)
                logger.warning(f"Product {product_id} no longer exists in database")
                continue
            
            # Convert price to float for template compatibility
            price = float(item['price'])
            quantity = item['quantity']
            total_price = price * quantity
            
            yield {
                'product': product,
                'price': price,
                'quantity': quantity,
                'total_price': total_price
            }
        
        # Remove deleted products after iteration
        if deleted_product_ids:
            for product_id in deleted_product_ids:
                logger.warning(f"Removing deleted product {product_id} from cart")
                del self.cart[product_id]
            self.save()

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Calculate the total cost of the items in the cart.
        """
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())

    def get_total_quantity(self):
        """
        Return total quantity of all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def clear(self):
        """
        Remove cart from session
        """
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True