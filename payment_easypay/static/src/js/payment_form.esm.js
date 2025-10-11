/* eslint-disable jsdoc/check-tag-names */
/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import paymentForm from "@payment/js/payment_form";

paymentForm.include({
    easypayCheckoutInstance: null,

    async _processRedirectFlow(
        providerCode,
        paymentOptionId,
        paymentMethodCode,
        processingValues
    ) {
        if (providerCode !== "easypay") {
            return await this._super(...arguments);
        }

        // Check if this is Single Payment flow (has payment URL) or Checkout flow (has manifest)
        if (processingValues.easypay_payment_url) {
            // Single Payment - use standard redirect flow
            console.log(
                "EasyPay: Using Single Payment flow - redirecting to:",
                processingValues.easypay_payment_url
            );
            return await this._super(...arguments);
        }

        // Checkout flow - load SDK and render inline
        console.log("EasyPay: Using Checkout flow with SDK");
        const manifest = processingValues.checkout_manifest;
        const checkoutId = processingValues.checkout_id;
        const apiUrl = processingValues.api_url;

        if (!manifest || !checkoutId || !apiUrl) {
            console.error("EasyPay: Missing checkout configuration");
            this._displayErrorDialog(
                _t("Configuration Error"),
                _t("Missing payment configuration. Please try again.")
            );
            this._enableButton();
            return;
        }

        const radio = document.querySelector('input[name="o_payment_radio"]:checked');
        const inlineForm = this._getInlineForm(radio);

        if (!inlineForm) {
            console.error("EasyPay: Inline form container not found");
            this._displayErrorDialog(
                _t("Configuration Error"),
                _t("Payment form container not found. Please try again.")
            );
            this._enableButton();
            return;
        }

        inlineForm.innerHTML = '<div id="easypay-checkout"></div>';

        try {
            // Wait for SDK to load from template script tag
            let attempts = 0;
            while (!window.easypayCheckout && attempts < 50) {
                await new Promise((resolve) => setTimeout(resolve, 100));
                attempts++;
            }

            if (!window.easypayCheckout || !window.easypayCheckout.startCheckout) {
                throw new Error("EasyPay Checkout SDK not loaded after 5 seconds");
            }

            const isTestMode = apiUrl.includes("test");

            this.easypayCheckoutInstance = window.easypayCheckout.startCheckout(
                manifest,
                {
                    id: "easypay-checkout",
                    display: "inline",
                    testing: isTestMode,
                    onSuccess: (successInfo) => {
                        console.log("EasyPay: Payment success", successInfo);
                        window.location = `/payment/easypay/checkout/success?id=${checkoutId}`;
                    },
                    onError: (error) => {
                        console.error("EasyPay: Payment error", error);
                        this._displayErrorDialog(
                            _t("Payment Error"),
                            _t("An error occurred during payment processing.")
                        );
                        this._enableButton();
                    },
                    onClose: () => {
                        console.log("EasyPay: Checkout closed");
                        window.location = `/payment/easypay/checkout/cancel?id=${checkoutId}`;
                    },
                }
            );
        } catch (error) {
            console.error("EasyPay: Error loading Checkout SDK", error);
            this._displayErrorDialog(
                _t("Payment Error"),
                _t("Could not load payment form. Please try again.")
            );
            this._enableButton();
        }
    },
});
