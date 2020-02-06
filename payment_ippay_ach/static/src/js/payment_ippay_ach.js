odoo.define('payment_ippay_ach.ippay_ach_payment', function(require) {
    "use strict";

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var PaymentForm = require('payment.payment_form');
    var rpc = require('web.rpc');

    var _t = core._t;
    var qweb = core.qweb;

    PaymentForm.include({

        events: _.extend({}, PaymentForm.prototype.events, {
            'click #o_payment_form_pay': 'payEvent',
        }),

        payEvent: function (ev) {
            var checked_radio = this.$('input[type="radio"]:checked');
            if (checked_radio.length === 1) {
                checked_radio = checked_radio[0];
            }
            var acquirer_id = this.getAcquirerIdFromRadio(checked_radio);
            var fields = ['provider']
            var domain = [['id','=',acquirer_id]];
            rpc.query({
                model: 'payment.acquirer',
                method: 'search_read',
                args: [domain, fields],
            }).then(function(record){
                if(record[0]['provider'] == 'ippay_ach'){
                    $('.ippay_ach_acquirer').val(acquirer_id)
                }
            })
            ev.preventDefault();
            if($(".selected_token_id").val().length > 0){
                $('.new_acc_dtl').html('')
            }
            return this._super.apply(this, arguments);
        },
    });

    $(".new").on('click', function(){
        $(".selected_token_id").val()
        $(".defualt_acc_dtl").addClass('d-none')
        $(".new_acc_dtl").removeClass('d-none')
    })

    $(".back").on('click', function(){
        $(".selected_token_id").val()
        $(".defualt_acc_dtl").removeClass('d-none')
        $(".new_acc_dtl").addClass('d-none')
    })

    $(".token_id").change(function (e){
        $(".selected_token_id").val($(this). children("option:selected"). val())
    })

    $('.new_acc_dtl').on('keypress', '#aba', function (evt) {
        var charCode = (evt.which) ? evt.which : evt.keyCode
        if (charCode > 31 && (charCode < 48 || charCode > 57))
            return false;

        return true;
    })

});

