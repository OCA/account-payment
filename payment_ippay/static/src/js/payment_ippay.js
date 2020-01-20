odoo.define('payment_ippay.ippay_payment', function(require) {
    "use strict";

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var PaymentForm = require('payment.payment_form');

    var _t = core._t;
    var qweb = core.qweb;

    PaymentForm.include({

        events: _.extend({}, PaymentForm.prototype.events, {
            'click #o_payment_form_pay': 'payEvent',
        }),

        payEvent: function (ev) {
            ev.preventDefault();
            if($(".selected_token_id").val().length > 0){
                $('.new_card_dtl').html('')
            }
            return this._super.apply(this, arguments);
        },
    });

    $(".new").on('click', function(){
        $(".selected_token_id").val()
        $(".defualt_dtl").addClass('d-none')
        $(".new_card_dtl").removeClass('d-none')
    })

    $(".token_id").change(function (e){
        $(".selected_token_id").val($(this). children("option:selected"). val())
    })

});

