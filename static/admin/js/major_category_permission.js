(function($) {
    'use strict';
    
    function toggleMajorCategoryCheckboxes(permission) {
        var checkboxesContainer = $('#major-category-checkboxes').closest('.form-row, .form-group, fieldset');
        
        if (permission === 'not_allowed') {
            checkboxesContainer.hide();
            // Uncheck all checkboxes
            $('#major-category-checkboxes input[type="checkbox"]').prop('checked', false);
        } else {
            checkboxesContainer.show();
        }
    }
    
    // Initialize on page load
    $(document).ready(function() {
        var permissionSelect = $('.major-category-permission-select');
        if (permissionSelect.length) {
            var currentValue = permissionSelect.val();
            toggleMajorCategoryCheckboxes(currentValue);
            
            // Handle change event
            permissionSelect.on('change', function() {
                toggleMajorCategoryCheckboxes($(this).val());
            });
        }
    });
    
    // Make function globally available
    window.toggleMajorCategoryCheckboxes = toggleMajorCategoryCheckboxes;
    
})(django.jQuery);
