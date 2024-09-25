/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {AccountPaymentField} from "@account/components/account_payment_field/account_payment_field";
import {patch} from "@web/core/utils/patch";
import {localization} from "@web/core/l10n/localization";
import {useService} from "@web/core/utils/hooks";

const {Component} = owl;

class PaymentAmountPopOver extends Component {}
PaymentAmountPopOver.template = "PaymentAmountPopOver";

patch(AccountPaymentField.prototype, {
    setup() {
        super.setup();
        this.widgetPopover = useService("popover");
        this.orm = useService("orm");
    },
    async popoverPartialOutstanding(ev, id) {
        for (
            var i = 0;
            i <
            this.props.record.data.invoice_outstanding_credits_debits_widget.content
                .length;
            i++
        ) {
            var k =
                this.props.record.data.invoice_outstanding_credits_debits_widget
                    .content[i];
            if (k.id === id) {
                this.popoverCloseFn = this.widgetPopover.add(
                    ev.currentTarget,
                    PaymentAmountPopOver,
                    {
                        title: _t("Enter the payment amount"),
                        id: id,
                        amount: k.amount_formatted,
                        placeholder: k.amount_formatted,
                        move_id: this.props.record.data.id,
                        _onOutstandingCreditAssign:
                            this._onOutstandingCreditAssign.bind(this),
                    },
                    {
                        position: localization.direction === "rtl" ? "bottom" : "left",
                    }
                );
                break; // Exit the loop once the match is found
            }
        }
    },
    async _onOutstandingCreditAssign(ev) {
        var id = parseInt($(ev.target).data("id"));
        var move_id = parseInt($(ev.target).data("move_id"));
        var payment_amount =
            parseFloat(document.getElementById("paid_amount").value) || 0.0;
        var context = {
            paid_amount: -payment_amount,
        };
        await this.orm.call(
            "account.move",
            "js_assign_outstanding_line",
            [move_id, id],
            {context: context}
        );
        this.popoverCloseFn();
        this.popoverCloseFn = null;
        await this.props.record.model.root.load();
        this.props.record.model.notify();
    },
});
