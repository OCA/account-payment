odoo.define('account_payment_slimpay.slimpay', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;
    var qweb = core.qweb;
    ajax.loadXML('/account_payment_slimpay/static/src/xml/slimpay_templates.xml', qweb);

    require('web.dom_ready');

    var access_token = ($("input[name='access_token']").val()
                        || $("input[name='token']").val()
                        || '');
    var acquirer_id = parseInt($(
      'form[provider="slimpay"] #acquirer_slimpay').val());

    ajax.jsonRpc('/payment/slimpay_transaction/' + acquirer_id,
                 'call', {access_token: access_token})
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
