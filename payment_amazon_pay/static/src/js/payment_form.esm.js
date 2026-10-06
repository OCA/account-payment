/* global amazon, document, window */

import {loadJS} from "@web/core/assets";
import paymentForm from "@payment/js/payment_form";

paymentForm.include({
    _amazonPayButton: null,

    async _prepareInlineForm(_providerId, providerCode) {
        if (providerCode !== "amazon_pay") {
            this._getAmazonWrapper()?.remove();
            this._amazonPayButton = null;
            return this._super(...arguments);
        }
        if (window.self !== window.top) return;

        this._hideInputs();

        const submitBtn = this._getSubmitBtn();
        this._renderAmazonPayPlaceholder(submitBtn);

        const radio = this.el.querySelector('input[name="o_payment_radio"]:checked');
        const values = JSON.parse(radio.dataset.amazonPayInlineFormValues);

        try {
            await loadJS(values.checkout_js_url);
            this._renderAmazonPayButton(values.amazon_pay_cfg, submitBtn);
        } catch {
            this._getAmazonWrapper()?.remove();
        }
    },

    _renderAmazonPayPlaceholder(submitBtn) {
        this._getAmazonWrapper()?.remove();
        const placeholder = document.createElement("div");
        placeholder.id = "o_amazon_pay_inline";
        placeholder.className =
            "w-100 d-flex justify-content-center align-items-center py-3";
        placeholder.innerHTML =
            '<i class="fa fa-spinner fa-spin fa-lg text-muted"></i>';
        if (submitBtn?.parentElement) {
            submitBtn.parentElement.insertBefore(placeholder, submitBtn);
        }
    },

    _renderAmazonPayButton(cfg, submitBtn) {
        this._getAmazonWrapper()?.remove();

        const wrapper = document.createElement("div");
        wrapper.id = "o_amazon_pay_inline";
        wrapper.className = "w-100";
        wrapper.innerHTML = '<div id="o_amazon_pay_button" class="w-100"></div>';

        if (submitBtn?.parentElement) {
            submitBtn.parentElement.insertBefore(wrapper, submitBtn);
        } else {
            (document.querySelector("#o_payment_form") || document.body).appendChild(
                wrapper
            );
        }

        this._amazonPayButton = amazon.Pay.renderButton("#o_amazon_pay_button", cfg);
        this._amazonPayButton.onClick(async () => {
            if (this._getSubmitBtn()?.disabled) {
                return;
            }
            await this._submitForm(new window.Event("AmazonPayClickEvent"));
        });
    },

    _processRedirectFlow(
        providerCode,
        _paymentOptionId,
        _paymentMethodCode,
        processingValues
    ) {
        if (providerCode !== "amazon_pay") {
            return this._super(...arguments);
        }

        const checkoutConfig =
            processingValues.amazon_pay_cfg?.createCheckoutSessionConfig;
        if (!checkoutConfig || !this._amazonPayButton) {
            this._enableButton();
            return;
        }

        this._amazonPayButton.initCheckout({
            createCheckoutSessionConfig: checkoutConfig,
        });
    },

    _getSubmitBtn() {
        return document.querySelector('button[name="o_payment_submit_button"]');
    },

    _getAmazonWrapper() {
        return document.getElementById("o_amazon_pay_inline");
    },
});
