odoo.define("pos_customer_wallet.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    models.load_fields("res.partner", ["customer_wallet_balance"]);
    models.load_fields("account.journal", ["is_customer_wallet_journal"]);
});
