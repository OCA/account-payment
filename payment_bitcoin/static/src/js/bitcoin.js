odoo.define('payment_bitcoin.bitcoin', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;

    require('web.dom_ready');
    if (!$('.o_payment_form').length) {
        return $.Deferred().reject("DOM doesn't contain '.o_payment_form'");
    }

    var $payment_method = $("span:contains('Bitcoin')").siblings('input');
    $payment_method.click(function (ev) {
        var $method_id = $(ev.currentTarget).val();
        var $method_name = $(ev.currentTarget).parent('label').find('span').text();

        $('tr[id="payment_bitcoin"]').remove();
        console.log($method_name);
        if ($method_name=='Bitcoin')
        {
            var $order_id = $('span[data-oe-model="sale.order"][data-oe-field="amount_total"]').attr('data-oe-id');
            var $order_ref = $('input[name="reference"]').attr('value');

            console.log($order_id);
            console.log($order_ref);
            ajax.jsonRpc("/payment_bitcoin/rate", 'call', {'order_id': $order_id, 'order_ref': $order_ref})
            .then(function (data) {
                console.log(data);
                if (data === false)
                {
                    alert(_t("Payment method Bitcoin is currently unavailable."));
                    $(ev.currentTarget).attr('disabled', 'disabled');
                    $(ev.currentTarget).prop('checked', false);
                }
                else
                {
                    $('div[id="order_total_bitcoin"]').remove();
                    var html = '<div class="row" id="order_total_bitcoin"><span class="col-xs-6 text-right h4 mt0"></span><span class="col-xs-6 text-right-not-xs text-left-xs h4 mt0" style="white-space: nowrap;">';
                    html += '<h4><span style="white-space: nowrap;" id="payment_bitcoin"><span class="oe_currency_value">='+ data[1] +'</span>&nbsp;'+data[2]+'</span></h4></span></div>';
                    var row = $('div[id="order_total"]');
                        $(html).insertAfter(row);
                }
            });
        }
    });


});
