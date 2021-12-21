odoo.define("account_payment_widget_amount.payment", function (require) {
    "use strict";

    var AbstractField = require("web.AbstractField");
    var core = require("web.core");
    var field_utils = require("web.field_utils");
    var account_payment = require("account.payment");

    var QWeb = core.qweb;

    account_payment.ShowPaymentLineWidget.include({
        events: _.extend(
            {
                "click .outstanding_credit_assign": "_dummyEventListener",
            },
            AbstractField.prototype.events
        ),

        _render: function () {
            this._super.apply(this, arguments);
            var self = this;
            var info = JSON.parse(this.value);
            if (!info) {
                this.$el.html("");
                return;
            }
            _.each(info.content, function (k, v) {
                k.index = v;
                k.amount = field_utils.format.float(k.amount, {digits: k.digits});
                if (k.date) {
                    k.date = field_utils.format.date(
                        field_utils.parse.date(k.date, {}, {isUTC: true})
                    );
                }
            });
            _.each(this.$(".outstanding_credit_assign"), function (k, v) {
                var content = info.content[v];
                var options = {
                    content: function () {
                        var $content = $(
                            QWeb.render("PaymentAmountPopOver", {
                                id: content.id,
                                currency: content.currency,
                                position: content.position,
                                amount: content.amount,
                            })
                        );
                        $content
                            .filter(".js_payment_amount")
                            .on("click", self._onOutstandingCreditAssign.bind(self));
                        return $content;
                    },
                    html: true,
                    placement: function () {
                        return $(window).width() <= 1080 ? "bottom" : "left";
                    },
                    title: "Enter the payment amount",
                    trigger: "click",
                    delay: {show: 0, hide: 100},
                    container: $(k).parent(),
                };
                $(k).popover(options);
                $(k).on("shown.bs.popover", function () {
                    document.getElementById("paid_amount").placeholder = $(this)
                        .parent()
                        .find("#paid_amount")
                        .attr("amount");
                });
            });
        },
        // --------------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------------

        /**
         * @private
         * @override
         * @param {MouseEvent} event
         */
        _onOutstandingCreditAssign: function (event) {
            var self = this;
            var id = parseInt($(event.target).attr("id"), 10);
            var payment_amount =
                parseFloat(document.getElementById("paid_amount").value) || 0.0;
            var context = {
                paid_amount: payment_amount,
            };
            this._rpc({
                model: "account.move",
                method: "js_assign_outstanding_line",
                args: [JSON.parse(this.value).move_id, id],
                context: context,
            }).then(function () {
                self.trigger_up("reload");
            });
        },
        _dummyEventListener: function (event) {
            event.stopPropagation();
            event.preventDefault();
        },
    });
});
