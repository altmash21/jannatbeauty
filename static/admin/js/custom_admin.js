document.addEventListener('DOMContentLoaded', function () {
    console.log('Custom Admin Dashboard Loaded');

    // Example: Add interactivity to widgets
    const widgets = document.querySelectorAll('.widget');
    widgets.forEach(widget => {
        widget.addEventListener('click', () => {
            alert('Widget clicked!');
        });
    });
});