odoo.define('payment_ippay.ippay_payment', function(require) {
    "use strict";

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var core = require('web.core');

    var _t = core._t;
    var qweb = core.qweb;

    $(".not_details").on('click', function(){
        if($(this).val() == 'new'){
            $(".new_dtl").removeClass('d-none')
            $(".defualt_dtl").addClass('d-none')
        }
        else{
            $(".new_dtl").addClass('d-none')
            $(".defualt_dtl").removeClass('d-none')
        }

    })

//     $('#ippayFormModal').on('hidden.bs.modal',function () {
//         hideSpinner();
//         hideMessage();
//     });
    
//     var observer = new MutationObserver(function(mutations, observer) {
//         for(var i=0; i<mutations.length; ++i) {
//             for(var j=0; j<mutations[i].addedNodes.length; ++j) {
//                 if(mutations[i].addedNodes[j].tagName.toLowerCase() === "form" && mutations[i].addedNodes[j].getAttribute('provider') == 'pinpayments') {
//                     display_ippay_form($(mutations[i].addedNodes[j]));
//                 }
//             }
//         }
//     });
 
//     function display_ippay_form(provider_form) {
//         // Open Checkout with further options
//         var payment_form = $('.o_payment_form');
//         if(!payment_form.find('i').length)
//             payment_form.append('<i class="fa fa-spinner fa-spin"/>');
//             payment_form.attr('disabled','disabled');

//         var payment_tx_url = payment_form.find('input[name="prepare_tx_url"]').val();
//         var acquirer_id = parseInt(provider_form.find('#acquirer_ippay').val()) || false;
//         var access_token = $("input[name='access_token']").val() || $("input[name='token']").val() || '';

//         ajax.jsonRpc(payment_tx_url, 'call', {
//             acquirer_id: acquirer_id,
//             access_token: access_token,
//         }).then(function(data) {
//             try {
//                 provider_form[0].innerHTML = data;
//                 var world_form = provider_form[0]
//             } catch (e) {};
//         }).done(function () {
//             $('#ippayFormModal').modal('show')
//             // $('.address1').val($("input[name='pin_billing_address']").val())
//             // $('.city').val($("input[name='pin_partner_city']").val())
//             // $('.postcode').val($("input[name='pin_partner_zip']").val())
//             // $('.state').val($("input[name='pin_partner_state']").val())
//             // $('.country').val($("input[name='pin_billing_country']").val())
//             // $('.order').val($("input[name='invoice_num']").val())
//             // $('.customerName').val($("input[name='pin_billing_partner']").val())
//             // $('.amount').val($("input[name='pin_amount']").val())
//             // $('.currency').val($("input[name='pin_currency']").val())
//             // $('.email').val($("input[name='pin_billing_partner_email']").val())
//             // $('.tx_ref').val($("input[name='invoice_num']").val())
//             // $('.return_url').val($("input[name='pin_return_url']").val())
//             // $('.tx_url').val($("input[name='pin_tx_url']").val())
//             $('.secret_key').val($("input[name='pin_secret_key']").val())
//             var pin_form = document.getElementById('pinpayment-form');
            
//         });
//     }

//     function showSpinner() {
//         $('#spinner-container').show();
//         $('#ippaypayment-form').hide();
//     };

//     function hideSpinner() {
//         $('#spinner-container').hide();
//         $('#ippaypayment-form').show();
//     };

//     function showMessage(message) {
//         $('#message-text').text(message);
//         $('#ippaypayment-form').hide();
//         $('#spinner-container').hide();
//         $('#message-container').show();
//     };

//     function hideMessage() {
//         $('#message-container').hide();
//         $('#pinpayment-form').show();
//     };

//     $.getScript("https://cdn.pinpayments.com/pin.v2.js", function(data, textStatus, jqxhr) {
//         observer.observe(document.body, {childList: true});
//         display_pin_form($('form[provider="pinpayments"]'));
//     });
    
});

// $(document).ready(function () {
//     var today_date = new Date()
//     var month = today_date.getMonth() + 1
//     var year = today_date.getFullYear()
//     $('#cc-expiry-month').change(function(){
//         if(($('#cc-expiry-month').val()) > 12){
//             $('.error').append($("<p> Please Enter validate month </p>"))
//             $('#cc-expiry-month').val('');
//             $('#cc-expiry-month').focus();
//         }
//         else if($('#cc-expiry-month').val() <= 0){
//             $('.error').append($("<p>Please Enter validate formate of month Eg : 0"+ $('#cc-expiry-month').val() +" </p>"))
//             $('#cc-expiry-month').val('');
//             $('#cc-expiry-month').focus();
//         }
//         else if(($('#cc-expiry-year').val()) && ($('#cc-expiry-year').val() == year) && ($('#cc-expiry-month').val() < month)){
//             $('.error').append($("<p>Your card Expired</p>"))
//             $('#cc-expiry-month').val('');
//             $('#cc-expiry-month').focus();
//         }
//         if(($('#cc-expiry-month').val()).length < 2  && ($('#cc-expiry-month').val()).length == 1){
//             $('#cc-expiry-month').val('0' + $('#cc-expiry-month').val());
//         }

//     });
//     $('#cc-expiry-month').focus(function(){
//          $('.error > p').remove();
//     });
//     $('#cc-expiry-year').change(function(){
//         if(($('#cc-expiry-year').val()).length < 4 || $('#cc-expiry-year').val() <= 0){
//             $('.error').append($("<p>Please Enter validate formate of year Eg : 2020 </p>"))
//             $('#cc-expiry-year').val('');
//             $('#cc-expiry-year').focus();
//         }
//         else if($('#cc-expiry-year').val() < year){
//             $('#cc-expiry-year').val('');
//             $('.error').append($("<p>Your card Expired</p>"))
//             $('#cc-expiry-year').focus();
//         }
//         else if(($('#cc-expiry-month').val()) && ($('#cc-expiry-year').val() == year) && ($('#cc-expiry-month').val() < month)){
//             $('.error').append($("<p>Your card Expired</p>"))
//             $('#cc-expiry-year').val('');
//             $('#cc-expiry-year').focus();
//         }
//     });
//     $('#cc-expiry-year').focus(function(){
//          $('.error > p').remove();
//     });
//     $("#cc-name").keypress(function(event){
//         var inputValue = event.which;
//         // allow letters and whitespaces only.
//         if(!(inputValue >= 65 && inputValue <= 120) && (inputValue != 32 && inputValue != 0)) {
//             event.preventDefault();
//         }
//     });
// })


