/* global amazon, window */
(function () {
    "use strict";
    var cfg = JSON.parse(window.document.getElementById("amazon-pay-cfg").textContent);
    function render() {
        amazon.Pay.renderButton("#o_amazon_pay_button", cfg);
    }
    if (typeof amazon === "undefined") {
        window.document
            .getElementById("o_amazon_pay_sdk")
            .addEventListener("load", render);
    } else {
        render();
    }
})();
