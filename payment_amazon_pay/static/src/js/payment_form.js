/* global document, window */
/** @odoo-module */

import "@payment/js/payment_form";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PaymentForm.include({
    _amazonPayLoadPromise: null,
    _amazonPayHidden: false,

    async start() {
        await this._super(...arguments);

        // Skip auto-load when inside an iframe (e.g. website editor preview) to
        // avoid navigating the preview frame to Amazon's domain on credential errors.
        if (window.self !== window.top) return;

        const amazonRadio = this.el.querySelector(
            'input[name="o_payment_radio"][data-provider-code="amazon_pay"]'
        );
        if (!amazonRadio) return;

        if (amazonRadio.checked) {
            await this._selectPaymentOption({target: amazonRadio});
        } else {
            this._amazonPayLoadPromise = this._loadAmazonPayButton(amazonRadio, true);
        }
    },

    async _selectPaymentOption(ev) {
        const checkedRadio = ev.target;
        if (this._getProviderCode(checkedRadio) !== "amazon_pay") {
            this._getAmazonWrapper()?.remove();
            const submitBtn = this._getSubmitBtn();
            if (submitBtn) submitBtn.classList.remove("d-none");
            this._amazonPayLoadPromise = null;
            await this._super(...arguments);
            return;
        }

        this._collapseInlineForms();
        // Prevent website_sale_charge_payment_fee from navigating away: that
        // module redirects when the selected provider changes, but Amazon Pay
        // renders its button inline and must stay on this page.
        this.$selectedProvider = checkedRadio;
        const submitBtn = this._getSubmitBtn();
        if (submitBtn) submitBtn.classList.add("d-none");

        const existingWrapper = this._getAmazonWrapper();
        if (existingWrapper && this._amazonPayLoadPromise === null) {
            existingWrapper.style.display = "";
            return;
        }

        if (this._amazonPayLoadPromise !== null) {
            await this._amazonPayLoadPromise;
            this._amazonPayLoadPromise = null;
            const wrapper = this._getAmazonWrapper();
            if (wrapper) {
                wrapper.style.display = "";
                return;
            }
        }

        this._renderAmazonPayPlaceholder(submitBtn);
        await this._loadAmazonPayButton(checkedRadio, false);
    },

    async _loadAmazonPayButton(radio, hidden) {
        this._amazonPayHidden = hidden;
        const previousFlow = this.paymentContext.flow;
        this.paymentContext.flow = "redirect";
        this.paymentContext.paymentOptionId = this._getPaymentOptionId(radio);
        this.paymentContext.providerCode = "amazon_pay";
        this.paymentContext.paymentMethodCode = this._getPaymentMethodCode(radio);
        this.paymentContext.providerId = this._getProviderId(radio);
        this.paymentContext.paymentMethodId = this._getPaymentOptionId(radio);
        this.paymentContext.tokenizationRequested = false;

        try {
            const flowPromise = this._initiatePaymentFlow(
                "amazon_pay",
                this.paymentContext.paymentOptionId,
                this.paymentContext.paymentMethodCode,
                "redirect"
            );
            this.paymentContext.flow = previousFlow;
            await flowPromise;
        } catch {
            this._getAmazonWrapper()?.remove();
            if (!hidden) {
                const submitBtn = this._getSubmitBtn();
                if (submitBtn) submitBtn.classList.remove("d-none");
            }
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

    _processRedirectFlow(
        providerCode,
        _paymentOptionId,
        _paymentMethodCode,
        processingValues
    ) {
        if (providerCode !== "amazon_pay") {
            return this._super(...arguments);
        }

        const cfg = processingValues.amazon_pay_cfg;
        const sdkUrl = processingValues.checkout_js_url;

        this._getAmazonWrapper()?.remove();

        if (!cfg || !sdkUrl) {
            if (!this._amazonPayHidden) this._showInputs();
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.id = "o_amazon_pay_inline";
        wrapper.className = "w-100";
        if (this._amazonPayHidden) wrapper.style.display = "none";
        wrapper.innerHTML = '<div id="o_amazon_pay_button" class="w-100"></div>';

        const submitBtn = this._getSubmitBtn();
        if (submitBtn?.parentElement) {
            submitBtn.parentElement.insertBefore(wrapper, submitBtn);
        } else {
            (document.querySelector("#o_payment_form") || document.body).appendChild(
                wrapper
            );
        }

        const renderBtn = () => {
            // eslint-disable-next-line no-undef
            amazon.Pay.renderButton("#o_amazon_pay_button", cfg);
        };
        if (document.querySelector(`script[src="${sdkUrl}"]`)) {
            renderBtn();
        } else {
            const script = document.createElement("script");
            script.src = sdkUrl;
            script.onload = renderBtn;
            document.head.appendChild(script);
        }
    },

    _getSubmitBtn() {
        return document.querySelector('button[name="o_payment_submit_button"]');
    },

    _getAmazonWrapper() {
        return document.getElementById("o_amazon_pay_inline");
    },
});
