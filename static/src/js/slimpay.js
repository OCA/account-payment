odoo.define('payment_slimpay.slimpay', function(require) {
    "use strict";

    var ajax = require('web.ajax');

    console.log('SLIMPAY JAVASCRIPT MODULE LOADED!');

    $('#pay_slimpay').on('click', function(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        var $form = $(ev.currentTarget).parents('form');
        var acquirer = $(ev.currentTarget)
            .parents('div.oe_sale_acquirer_button').first();
        var acquirer_id = acquirer.data('id');
        if (! acquirer_id) {
            return false;
        }
        var acquirer_token = acquirer.attr('data-token');
        var tx_type = acquirer
            .find('input[name="odoo_save_token"]')
            .is(':checked') ? 'form_save' : 'form';
        var params = {'tx_type': tx_type};
        if (acquirer_token) {
            params.token = acquirer_token;
        }

        if(!$(this).find('i').length)
            $(this).append('<i class="fa fa-spinner fa-spin"/>');
            $(this).attr('disabled','disabled');

        ajax.jsonRpc('/payment/slimpay_transaction/' + acquirer_id,
                     'call', params)
            .done(function (data) {
                window.location.href = data;
            }).fail(function() {
                console.log('Please add error display... args: ', arguments);
            });
        return false;
    });

});
