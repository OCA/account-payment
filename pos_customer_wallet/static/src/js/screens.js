odoo.define("pos_customer_wallet.screens", function (require) {
    "use strict";
    var core = require("web.core");
    var screens = require("point_of_sale.screens");

    var _t = core._t;

    screens.PaymentScreenWidget.include({
        customer_changed: function () {
            this._super();
            if (this.pos.config.is_enabled_customer_wallet) {
                var client = this.pos.get_client();
                this.$(".balance").text(
                    client ? this.format_currency(client.customer_wallet_balance) : ""
                );
                this.$(".balance-header").text(
                    client ? _t("Customer Wallet Balance") : ""
                );
            }
        },
        find_customer_wallet_payment_method() {
            // This is fairly naive.
            for (var i = 0; i < this.pos.cashregisters.length; i++) {
                if (this.pos.cashregisters[i].journal.is_customer_wallet_journal) {
                    return this.pos.cashregisters[i];
                }
            }
            return null;
        },
        order_is_valid: function () {
            if (!this._super()) {
                return false;
            }

            var client = this.pos.get_client();
            var customer_wallet_payment_method =
                this.find_customer_wallet_payment_method();
            if (!client && customer_wallet_payment_method) {
                this.gui.show_popup("error", {
                    title: _t("No customer selected"),
                    body: _t(
                        "Cannot user customer wallet payment method without selecting a customer.\n\n Please select a customer or use a different payment method."
                    ),
                });
                return false;
            }

            return true;
        },
    });
});
