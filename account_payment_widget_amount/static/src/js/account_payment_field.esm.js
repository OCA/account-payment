/** @odoo-module **/

import {AccountPaymentField} from "@account/components/account_payment_field/account_payment_field";
import {patch} from "@web/core/utils/patch";
import {localization} from "@web/core/l10n/localization";
const {Component} = owl;

class PaymentAmountPopOver extends Component {}
PaymentAmountPopOver.template = "PaymentAmountPopOver";

patch(AccountPaymentField.prototype, "account_partial_outstanding_payment", {
    async popoverPartialOutstanding(ev, id) {
        var self = this;
        _.each(this.props.value.content, function (k) {
            var recId = k.id === id;
            if (recId) {
                self.popoverCloseFn = self.popover.add(
                    ev.currentTarget,
                    PaymentAmountPopOver,
                    {
                        title: self.env._t("Enter the payment amount"),
                        id: id,
                        amount: k.amount_formatted,
                        placeholder: k.amount_formatted,
                        move_id: self.move_id,
                        _onOutstandingCreditAssign:
                            self._onOutstandingCreditAssign.bind(self),
                    },
                    {
                        position: localization.direction === "rtl" ? "bottom" : "left",
                    }
                );
            }
        });
    },
    async _onOutstandingCreditAssign(ev) {
        var self = this;
        var id = parseInt($(ev.target).data("id"));
        var move_id = parseInt($(ev.target).data("move_id"));
        var payment_amount =
            parseFloat(document.getElementById("paid_amount").value) || 0.0;
        var context = {
            paid_amount: payment_amount,
        };
        await this.orm
            .call("account.move", "js_assign_outstanding_line", [move_id, id], {
                context: context,
            })
            .then(function () {
                self.closePopover();
            });
        await this.props.record.model.root.load();
        this.props.record.model.notify();
    },
});
