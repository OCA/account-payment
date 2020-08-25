odoo.define('account_payment_slimpay.slimpay', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;
    var qweb = core.qweb;
    ajax.loadXML('/account_payment_slimpay/static/src/xml/slimpay_templates.xml', qweb);

    require('web.dom_ready');

    var token = ($("input[name='access_token']").val()
                 || $("input[name='token']").val()
                 || '');
    var acquirer_id = parseInt($(
      'form[provider="slimpay"] #acquirer_slimpay').val());

    // Search if the user wants to save the credit card information
    var form_save_token = $(
        '#o_payment_form_acq_' + acquirer_id + ' ' +
        'input[name="o_payment_form_save_token"]').prop('checked');

    var params = {
      tx_type: form_save_token ? 'form_save' : 'form',
      token: token,
    };

    ajax.jsonRpc('/payment/slimpay_transaction/' + acquirer_id,
                 'call', params)
        .done(function (data) {
            window.location.href = data;
        })
        .fail(function() {
            console.log('Slimpay transaction error! Args: ', arguments);
            var msg = (arguments && arguments[1] && arguments[1].data &&
                       arguments[1].data.message);
            var wizard = $(qweb.render(
              'slimpay.error', {'msg': msg || _t('Payment error')}));
            wizard.appendTo($('body')).modal({'keyboard': true});
        });

});
