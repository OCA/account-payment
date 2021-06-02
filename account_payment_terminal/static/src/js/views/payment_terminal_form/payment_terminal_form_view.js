odoo.define("account_payment_terminal.OCAPaymentTerminalFormView", function (require) {
    "use strict";

    var core = require("web.core");
    var BasicView = require("web.BasicView");
    var FormView = require("web.FormView");
    var viewRegistry = require("web.view_registry");
    var FormRenderer = require("web.FormRenderer");
    var OCAPaymentTerminalFormController = require("account_payment_terminal.OCAPaymentTerminalFormController");

    var _lt = core._lt;

    var OCAPaymentTerminalFormView = FormView.extend({
        config: _.extend({}, BasicView.prototype.config, {
            Renderer: FormRenderer,
            Controller: OCAPaymentTerminalFormController,
        }),
        display_name: _lt("Payment Terminal Form"),
        icon: "fa-edit",
        multi_record: false,
        withSearchBar: false,
        searchMenuTypes: [],
        viewType: "oca_payment_terminal_form",
        init: function () {
            this._super.apply(this, arguments);
        },
    });

    viewRegistry.add("oca_payment_terminal_form", OCAPaymentTerminalFormView);
    return OCAPaymentTerminalFormView;
});
