odoo.define('payment_slimpay.slimpay', function(require) {
    "use strict";

    var ajax = require('web.ajax');

    console.log('SLIMPAY JAVASCRIPT MODULE LOADED!');

    $('#pay_slimpay').on('click', function(e) {

        e.preventDefault();

        if(!$(this).find('i').length)
            $(this).append('<i class="fa fa-spinner fa-spin"/>');
            $(this).attr('disabled','disabled');

        ajax.jsonRpc("/payment/slimpay/create_sepa_direct_debit", 'call', {
                acquirer: $("input[name='acquirer']").val(),
                return_url: $("input[name='return_url']").val()
            }).done(function(data){
                console.log('DONE !', data);
                window.location.href = data;
            }).fail(function(){
                console.log('FAIL !', arguments);
            });

    });

});
