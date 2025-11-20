// Cart functionality
function addToCart(form, showNotification = true) {
    const formData = new FormData(form);
    const button = form.querySelector('button[type="submit"]');
    const originalText = button ? button.textContent : '';

    if (button) {
        button.textContent = 'Adding...';
        button.disabled = true;
    }

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (button) {
                    button.textContent = 'Added!';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 1200);
                }

                if (showNotification) {
                    // Update cart count in header
                    updateCartCount(data.cart_total_items);
                }

                // If this is a Buy Now request, redirect to cart
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
            } else {
                if (button) {
                    button.textContent = originalText;
                    button.disabled = false;
                }
                alert(data.message || 'Error adding to cart');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (button) {
                button.textContent = originalText;
                button.disabled = false;
            }
            alert('Network error occurred');
        });
}

function updateCartCount(count) {
    // Update cart count badge in header and mobile navbar
    const cartCountElements = document.querySelectorAll('.cart-count, .cart-badge, .cart-badge-mobile');
    cartCountElements.forEach(el => {
        el.textContent = count;
        // Always show the badge
        el.style.display = 'inline';
    });

    // Also call the base template's update function if it exists
    if (typeof updateCartCountDisplay === 'function') {
        updateCartCountDisplay(count);
    }
}

// Initialize cart functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Update cart count on page load
    fetch('/cart/count/')
        .then(response => response.json())
        .then(data => updateCartCount(data.count || 0))
        .catch(error => console.log('Cart count load error:', error));

    // Handle all Add to Cart buttons
    document.addEventListener('click', function (e) {
        if (e.target.matches('button[type="submit"]') &&
            e.target.textContent.trim().includes('Add to Cart')) {
            e.preventDefault();
            const form = e.target.closest('form');
            if (form && (form.action.includes('/cart/add/') || form.action.includes('cart_add'))) {
                addToCart(form, true);
            }
        }
    });

    // Handle Buy Now buttons - let them submit normally or use AJAX with redirect
    document.addEventListener('click', function (e) {
        if (e.target.matches('button[type="submit"]') &&
            e.target.textContent.trim().includes('Buy Now')) {
            e.preventDefault();
            const form = e.target.closest('form');
            if (form && (form.action.includes('/cart/add/') || form.action.includes('cart_add'))) {
                addToCart(form, false); // No notification, will redirect
            }
        }
    });
});