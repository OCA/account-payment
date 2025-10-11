To configure this module, you need to:

1.  Go to **Accounting \> Configuration \> Payment Providers** or
    **Website \> Configuration \> Payment Providers**
2.  Search for **EasyPay** and open the provider form
3.  Fill in the required credentials:
    - **Account ID**: Your EasyPay Account ID (obtain from EasyPay
      dashboard)
    - **API Key**: Your EasyPay API Key (obtain from EasyPay dashboard)
    - **Payment Method**: Select the payment method you want to use
      (Credit Card, Multibanco, MB WAY, etc.)
    - **Use Checkout**: Enable this to use EasyPay's integrated checkout
      experience
4.  Configure the provider state:
    - Set to **Test Mode** to use the test environment
      (<https://api.test.easypay.pt>)
    - Set to **Enabled** to use the production environment
      (<https://api.prod.easypay.pt>)
5.  Save the configuration

For testing purposes, you can use the following credentials:

- **Account ID**: 2b0f63e2-9fb5-4e52-aca0-b4bf0339bbe6
- **API Key**: eae4aa59-8e5b-4ec2-887d-b02768481a92

**Note**: These test credentials only work in Test Mode.

## Webhook Configuration

To receive automatic payment status updates, configure the following
webhook URL in your EasyPay dashboard:

- **Webhook URL**: <https://yourdomain.com/payment/easypay/webhook>

This ensures that payment status changes are immediately reflected in
Odoo.

## Production Setup

### Get Production Credentials

1.  Sign up at <https://www.easypay.pt/>
2.  Complete merchant verification
3.  Get your production credentials from dashboard

### Configure for Production

1.  Open EasyPay provider in Odoo
2.  Update credentials with production values
3.  Change **State** to **Enabled**
4.  Configure webhook in EasyPay dashboard:

&nbsp;

    URL: https://yourdomain.com/payment/easypay/webhook
    Events: Generic, Transaction, Authorisation

5.  Test with real card (small amount)
6.  Publish the payment provider
