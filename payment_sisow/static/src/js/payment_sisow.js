//-*- coding: utf-8 -*-
//© 2017 Therp BV <http://therp.nl>
//License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
odoo.define('payment_sisow', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    jQuery(document).ready(function()
    {
        jQuery('#payment_method select.sisow_issuer').change(function()
        {
            var value = jQuery(this).val();
            ajax.jsonRpc('/payment/sisow/issuer/' + value);
            if(value)
            {
                jQuery(this).parents('form').removeClass('has-error');
            }
        });
    });
})
