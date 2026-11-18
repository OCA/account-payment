/* global amazon, window */

import {loadJS} from "@web/core/assets";
import {paymentExpressCheckoutForm} from "@payment/js/express_checkout_form";
import {rpc} from "@web/core/network/rpc";

paymentExpressCheckoutForm.include({
    async _prepareExpressCheckoutForm(providerData) {
        if (
            providerData.providerCode !== "amazon_pay" ||
            !this.paymentContext.amount ||
            !this.paymentContext.shippingInfoRequired
        ) {
            return this._super(...arguments);
        }
        this.amazonPayData = providerData;
        await loadJS(providerData.amazonPayCheckoutJsUrl);
        amazon.Pay.renderJSButton(
            `#o_amazon_pay_express_checkout_container_${providerData.providerId}`,
            {
                merchantId: providerData.amazonPayMerchantId,
                ledgerCurrency: providerData.amazonPayLedgerCurrency,
                checkoutLanguage: providerData.amazonPayCheckoutLanguage,
                sandbox: Boolean(providerData.amazonPaySandbox),
                productType: "PayAndShip",
                placement: "Cart",
                buttonColor: "Gold",
                estimatedOrderAmount: this._amazonPayPrice(
                    this.paymentContext.minorAmount
                ),
                checkoutSessionConfig: {
                    storeId: providerData.amazonPayStoreId,
                    scopes: [
                        "name",
                        "email",
                        "phoneNumber",
                        "billingAddress",
                        "shippingAddress",
                    ],
                    paymentDetails: {
                        paymentIntent: "AuthorizeWithCapture",
                        canHandlePendingAuthorization: false,
                    },
                },
                onInitCheckout: (event) => {
                    this.amazonPayBuyer = event.buyer || {};
                    return this._amazonPayUpdateShippingAddress(event.shippingAddress);
                },
                onShippingAddressSelection: (event) =>
                    this._amazonPayUpdateShippingAddress(event.shippingAddress),
                onDeliveryOptionSelection: (event) =>
                    this._amazonPaySelectDeliveryOption(event.deliveryOptions),
                onCompleteCheckout: (event) => this._amazonPayCompleteCheckout(event),
            }
        );
    },

    _amazonPayPrice(minorAmount) {
        const decimals = parseInt(this.amazonPayData.amazonPayDecimalPlaces, 10);
        return {
            amount: (minorAmount / 10 ** decimals).toFixed(decimals),
            currencyCode: this.amazonPayData.amazonPayLedgerCurrency,
        };
    },

    _amazonPayCartDetails() {
        const baseAmount = parseInt(this.paymentContext.minorAmount, 10);
        const shippingAmount = this.amazonPayDeliveryMethod.minorAmount;
        const discountAmount = -this.amazonPayDeliveryDiscount;
        return {
            totalBaseAmount: this._amazonPayPrice(baseAmount),
            totalTaxAmount: this._amazonPayPrice(0),
            totalShippingAmount: this._amazonPayPrice(shippingAmount),
            totalDiscountAmount: this._amazonPayPrice(discountAmount),
            totalChargeAmount: this._amazonPayPrice(
                baseAmount + shippingAmount - discountAmount
            ),
            deliveryOptions: this.amazonPayDeliveryMethods.map((dm) => ({
                id: String(dm.id),
                price: this._amazonPayPrice(dm.minorAmount),
                shippingMethod: {
                    shippingMethodName: dm.name,
                    shippingMethodCode: String(dm.id),
                },
                isDefault: dm.id === this.amazonPayDeliveryMethod.id,
            })),
        };
    },

    async _amazonPayUpdateShippingAddress(address) {
        try {
            const {delivery_methods, delivery_discount_minor_amount} = await rpc(
                this.paymentContext.shippingAddressUpdateRoute,
                {
                    partial_delivery_address: {
                        zip: address.postalCode,
                        city: address.city,
                        country: address.countryCode,
                        state: address.stateOrRegion,
                    },
                }
            );
            const minorAmount = await rpc(
                this.paymentContext.shippingAddressUpdateRoute + "/compute_taxes"
            );
            if (!delivery_methods.length || minorAmount.external_tax_error) {
                return {status: "error", reasonCode: "shippingAddressInvalid"};
            }
            this.paymentContext.minorAmount = minorAmount;
            this.amazonPayShippingAddress = address;
            this.amazonPayDeliveryMethods = delivery_methods;
            this.amazonPayDeliveryMethod = delivery_methods[0];
            this.amazonPayDeliveryDiscount = delivery_discount_minor_amount || 0;
            return this._amazonPayCartDetails();
        } catch {
            return {status: "error", reasonCode: "unknownError"};
        }
    },

    async _amazonPaySelectDeliveryOption(deliveryOption) {
        try {
            const result = await rpc("/shop/set_delivery_method", {
                dm_id: parseInt(deliveryOption.id, 10),
            });
            const minorAmount = await rpc(
                this.paymentContext.shippingAddressUpdateRoute + "/compute_taxes"
            );
            if (minorAmount.external_tax_error) {
                return {status: "error", reasonCode: "deliveryOptionInvalid"};
            }
            this.paymentContext.minorAmount = minorAmount;
            this.amazonPayDeliveryMethod = this.amazonPayDeliveryMethods.find(
                (dm) => String(dm.id) === deliveryOption.id
            );
            this.amazonPayDeliveryDiscount =
                parseInt(result.delivery_discount_minor_amount, 10) || 0;
            return this._amazonPayCartDetails();
        } catch {
            return {status: "error", reasonCode: "deliveryOptionInvalid"};
        }
    },

    _amazonPayOdooAddress(address) {
        return {
            name: address.name,
            email: this.amazonPayBuyer.email,
            phone: address.phoneNumber || this.amazonPayBuyer.phoneNumber,
            street: address.addressLine1,
            street2: [address.addressLine2, address.addressLine3]
                .filter(Boolean)
                .join(" "),
            zip: address.postalCode,
            city: address.city,
            country: address.countryCode,
            state: address.stateOrRegion,
        };
    },

    async _amazonPayCompleteCheckout(event) {
        try {
            this.paymentContext.partnerId = parseInt(
                await rpc(this.paymentContext.expressCheckoutRoute, {
                    billing_address: this._amazonPayOdooAddress(event.billingAddress),
                    shipping_address: this._amazonPayOdooAddress(
                        this.amazonPayShippingAddress
                    ),
                    shipping_option: {id: this.amazonPayDeliveryMethod.id},
                }),
                10
            );
            const {reference} = await rpc(
                this.paymentContext.transactionRoute,
                this._prepareTransactionRouteParams(this.amazonPayData.providerId)
            );
            await rpc("/payment/amazon_pay/finalize", {
                reference,
                checkout_session_id: event.amazonCheckoutSessionId,
                shipping_address: this.amazonPayShippingAddress,
            });
            window.location = "/payment/status";
            return {status: "success"};
        } catch {
            window.location = "/shop/cart";
            return {status: "error"};
        }
    },
});
