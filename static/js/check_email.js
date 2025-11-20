document.addEventListener('DOMContentLoaded', function () {
    var emailInput = document.querySelector('input[name="email"]');
    if (!emailInput) return;

    var lastValue = '';
    var timeout = null;

    var feedback = document.createElement('div');
    feedback.style.color = '#d9534f';
    feedback.style.fontSize = '0.95em';
    feedback.style.marginTop = '4px';
    feedback.style.display = 'none';
    emailInput.parentNode.appendChild(feedback);

    emailInput.addEventListener('input', function () {
        var value = emailInput.value.trim();
        if (value === lastValue) return;
        lastValue = value;
        feedback.style.display = 'none';
        if (timeout) clearTimeout(timeout);
        if (!value) return;
        timeout = setTimeout(function () {
            fetch('/accounts/ajax/check-email/?email=' + encodeURIComponent(value))
                .then(response => response.json())
                .then(data => {
                    if (data.taken) {
                        feedback.textContent = 'This email is already registered.';
                        feedback.style.display = 'block';
                    } else {
                        feedback.textContent = '';
                        feedback.style.display = 'none';
                    }
                })
                .catch(() => {
                    feedback.textContent = '';
                    feedback.style.display = 'none';
                });
        }, 400);
    });
});
