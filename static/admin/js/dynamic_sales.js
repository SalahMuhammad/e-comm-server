django.jQuery(function($) {
    var owner_select = $('#id_owner');
    var sale_select = $('#id_sale');
    
    owner_select.on('change', function() {
        var owner_id = $(this).val();
        
        // Clear current sale options
        sale_select.empty();
        
        if (owner_id) {
            // Fetch sales for selected owner
            $.getJSON('/admin/finance/payment/get_sales_for_owner/', {
                'owner_id': owner_id
            }, function(data) {
                // Add empty option
                sale_select.append($('<option value="">---------</option>'));
                
                // Add sales options
                $.each(data, function(index, item) {
                    sale_select.append(
                        $('<option></option>')
                            .attr('value', item.id)
                            .text(item.reference + ' - ' + item.total_amount)
                    );
                });
            });
        }
    });
});