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
        amount_paid_with_customer_wallet() {
            var order = this.pos.get_order();
            var cashregister = this.find_customer_wallet_payment_method();
            var total = 0;
            var lines = order.paymentlines.models;
            for (var i = 0; i < lines.length; i++) {
                if (lines[i].cashregister === cashregister) {
                    total += lines[i].amount;
                }
            }
            return total;
        },
        order_is_valid: function () {
            if (!this._super()) {
                return false;
            }

            var client = this.pos.get_client();
            var wallet_amount = this.amount_paid_with_customer_wallet();

            if (!client) {
                if (wallet_amount > 0) {
                    this.gui.show_popup("error", {
                        title: _t("No customer selected"),
                        body: _t(
                            "Cannot user customer wallet payment method without selecting a customer.\n\n Please select a customer or use a different payment method."
                        ),
                    });
                    return false;
                }
            } else {
                if (client.customer_wallet_balance - wallet_amount <= -0.00001) {
                    this.gui.show_popup("error", {
                        title: _t("Customer wallet balance not sufficient"),
                        body: _t(
                            "There is not enough balance in the customer's wallet to perform this order."
                        ),
                    });
                    return false;
                }
            }

            return true;
        },
        finalize_validation: function () {
            var wallet_amount = this.amount_paid_with_customer_wallet();
            var client = this.pos.get_client();

            client.customer_wallet_balance -= wallet_amount;

            this._super();
        },
    });
});
