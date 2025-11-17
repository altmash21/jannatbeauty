// Shared Buy Now functionality
function buyNow() {
    const form = document.getElementById('add-to-cart-form');
    if (!form) {
        console.error('Add to Cart form not found.');
        return;
    }

    const formData = new FormData(form);

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
                window.location.href = data.redirect_url || '/checkout';
            } else {
                alert(data.message || 'Error adding to cart');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Fallback to regular form submission
            form.submit();
        });
}