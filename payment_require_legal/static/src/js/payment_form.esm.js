/* Copyright 2026 Tecnativa - Pilar Vargas
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

import paymentForm from "@payment/js/payment_form";

paymentForm.include({
    events: {
        ...paymentForm.prototype.events,
        "change #payment_require_legal": "_onChangeLegalTerms",
    },

    /**
     * @override
     */
    async start() {
        await this._super(...arguments);
        this._updateSubmitButton();
    },

    /**
     * Keep the payment button disabled until the legal terms are accepted.
     */
    _onChangeLegalTerms() {
        this._updateSubmitButton();
    },

    _updateSubmitButton() {
        const legalTerms = this.el.querySelector("#payment_require_legal");
        const submitButton = this.el.querySelector(
            "button[name='o_payment_submit_button']"
        );
        if (legalTerms && submitButton) {
            submitButton.disabled = !legalTerms.checked;
        }
    },

    /**
     * Include the legal terms acceptance in the transaction parameters.
     *
     * @override
     */
    _prepareTransactionRouteParams() {
        const params = this._super(...arguments);
        const legalTerms = this.el.querySelector("#payment_require_legal");
        return {
            ...params,
            legal_terms_accepted: Boolean(legalTerms?.checked),
        };
    },

    /**
     * Prevent submission even if another payment widget enabled the button.
     *
     * @override
     */
    async _submitForm(ev) {
        const legalTerms = this.el.querySelector("#payment_require_legal");
        if (legalTerms && !legalTerms.checked) {
            ev.preventDefault();
            ev.stopPropagation();
            this._updateSubmitButton();
            return;
        }
        return this._super(...arguments);
    },
});
