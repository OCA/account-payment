This module lets ecommerce customers to pay with Bitcoin. During configuration, multiple Bitcoin addresses need to be entered. Each Bitcoin address is assigned to one order only and used only once. During checkout, when a customer chooses to pay with Bitcoin, the next available Bitcoin address will be assigned to the sales order and the amount to be paid in Bitcoin is calculated automatically. At the time of assigning a Bitcoin address, the current exchange rate is fetched from TODO and the configured Bitcoin rate is applied to it. This rate can be configured similarly to an additional payment fee. At the checkout confirmation page, the Bitcoin address and the amount to-be-payed is displayed to the customer. The amount and Bitcoin address can also be send to the customer in the order confirmation email. If a customer chooses to pay with Bitcoin but no Bitcoin address is available, an error is displayed.

Other than fetching the exchange rate, there is no online integration or Blockchain implementation to other services or the Bitcoin network. The actual Bitcoin Payments are not known to Odoo. Instead payments need to be confirmed manually, similarly to wire transfers.

In the backoffice a Bitcoin rate needs to be configured and several Bitcoin addresses to be entered.

Invoicing -> Configuration -> Bitcoin Adresses

When adding or importing Bitcoin addresses their validity is verified. The same Bitcoin address can't be added twice.

Bitcoin addresses are assigned to sales orders:

Invoicing -> Configuration -> Bitcoin Adresses -> Create

