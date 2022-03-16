odoo.define("account_payment_terminal.OCAPaymentTerminalFormController", function (
    require
) {
    "use strict";

    var rpc = require("web.rpc");
    var FormController = require("web.FormController");
    var core = require("web.core");

    var _lt = core._lt;

    var OCAPaymentTerminalFormController = FormController.extend({
        init: function () {
            this.transaction_id = null;
            this.oca_payment_terminal_id = null;
            this.proxy_url = null;
            this._super.apply(this, arguments);
        },
        _show_error: function (error_message) {
            this.$el.find("p").css("color", "red").text(error_message);
            console.error(error_message);
        },
        _show_success: function (success_message) {
            this.$el.find("p").css("color", "green").text(success_message);
        },
        _proxy_call: function (service, data, timeout) {
            return $.ajax({
                url: this.proxy_url + "/hw_proxy/" + service,
                dataType: "json",
                contentType: "application/json;charset=utf-8",
                data: JSON.stringify(data),
                method: "POST",
                timeout: timeout,
            });
        },
        _get_payment_info: function () {
            return rpc.query({
                model: this.model.loadParams.modelName,
                method: "get_payment_info",
                args: [[this.model.loadParams.res_id]],
            });
        },
        _confirm_payment: function (transaction) {
            return rpc.query({
                model: this.model.loadParams.modelName,
                method: "action_confirm_payment",
                args: [[this.model.loadParams.res_id], transaction.reference],
            });
        },
        _get_payment_terminal_transaction_start_data: function (payment_info) {
            this.proxy_url = payment_info.proxy_ip;
            var cid = Math.floor(Math.random() * 1000 * 1000 * 1000);
            var params = {
                payment_info: JSON.stringify(payment_info),
            };
            return {
                jsonrpc: "2.0",
                method: "call",
                params: params,
                id: cid,
            };
        },
        _set_transaction_status: function (transaction, timerId) {
            var self = this;
            if (transaction.success) {
                clearInterval(timerId);
                self._confirm_payment(transaction)
                    .then(function () {
                        self._show_success(_lt("Payment Successful"));
                    })
                    .catch(() => {
                        self._show_error(
                            _lt("Payment Successful but couldn't confirm it in odoo")
                        );
                    });
            } else if (transaction.success === false) {
                clearInterval(timerId);
                self._show_error(_lt("Transaction cancelled"));
            }
        },
        _poll_for_transaction_status: function () {
            var self = this;
            var timerId = setInterval(() => {
                var status_params = {};
                if (self.oca_payment_terminal_id) {
                    status_params.terminal_id = self.oca_payment_terminal_id;
                }
                this._proxy_call("status_json", {params: status_params}, 1000)
                    .done((drivers_status) => {
                        if ("result" in drivers_status) {
                            var d_status = drivers_status.result;
                            for (var driver_name in d_status) {
                                var driver = d_status[driver_name];
                                if (
                                    !driver.is_terminal ||
                                    !("transactions" in driver)
                                ) {
                                    continue;
                                }
                                for (var transaction_id in driver.transactions) {
                                    var transaction =
                                        driver.transactions[transaction_id];
                                    if (
                                        transaction.transaction_id ===
                                        self.transaction_id
                                    ) {
                                        self._set_transaction_status(
                                            transaction,
                                            timerId
                                        );
                                    }
                                }
                            }
                        }
                    })
                    .fail(() => {
                        self._show_error(_lt("Error querying terminal driver status"));
                        clearInterval(timerId);
                    });
            }, 1000);
        },
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._get_payment_info().then(function (payment_info) {
                    self.oca_payment_terminal_id = payment_info.oca_payment_terminal_id;
                    var data = self._get_payment_terminal_transaction_start_data(
                        payment_info
                    );
                    self._proxy_call("payment_terminal_transaction_start", data, 10000)
                        .done(function (response) {
                            if (response === false) {
                                self._show_error(
                                    _lt(
                                        "Failed to send the amount to pay to the payment terminal. Press the red button on the payment terminal and try again."
                                    )
                                );
                                return false;
                            } else if (
                                response instanceof Object &&
                                "result" in response &&
                                "transaction_id" in response.result
                            ) {
                                self.transaction_id = response.result.transaction_id;
                                self._poll_for_transaction_status();
                            }
                        })
                        .fail(function () {
                            self._show_error(_lt("Error starting payment transaction"));
                            return false;
                        });
                });
            });
        },
    });

    return OCAPaymentTerminalFormController;
});
