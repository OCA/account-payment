<!--
SPDX-FileCopyrightText: 2025 Mael Panouillot <panouillot.mael@gmail.com>

SPDX-License-Identifier: LGPL-3.0-or-later
-->

_This page is also available in French [here](https://codeberg.org/Nemael/tops/src/branch/18.0/README_FR.md)._

_Cette page est également disponible en Français [here](https://codeberg.org/Nemael/tops/src/branch/18.0/README_FR.md)._

---

# TOPS: Taler-Odoo Payment System

TOPS is an add-on for Odoo. It allows users to pay with Taler, similar to other existing payment integrations in Odoo.
The module integrates into and increase functionality of other existing Odoo modules (eCommerce, invoices, ticket sales, online payment, etc.). It also implements refunds to customers that used Taler to pay.

Installing this module enables merchants to accept payments from customers using their Taler Wallet, giving them the option to choose a payment system that respects their privacy.

It is available on the Odoo Apps store (https://apps.odoo.com/apps) PENDING LINK, as well as on the OCA community shop (https://odoo-community.org/shop) PENDING LINK

It has been built for Odoo 18, and will be updated to Odoo 19 once milestone 1.0 is reached.

---

## Tutorials and flow walkthrough

### Install or update the add-on on an already-existing Odoo installation

- There are multiple ways to install this add-on
  - Install from the OCA community shop
    - PENDING
  - Install from the Odoo Apps store
    - PENDING
  - Add the code yourself in your Odoo install (by cloning or downloading the release)
    - Clone this repository (git clone https://codeberg.org/Nemael/tops.git)
      - Preferably clone it in `{your Odoo install}/custom_addons`
        - Ensure that the `tops` directory is in `custom_addons`
    - Download the latest version from the releases (https://codeberg.org/Nemael/tops/releases)
      - Extract the zip file to `{your Odoo install}/custom_addons`
      - Ensure that the `tops` directory is in `custom_addons`
    - Note: the code can be stored anywhere, but it's easier store it within the Odoo folder
- In the command line you used to start Odoo, specify the path to this add-on by adding the argument `--addons-path=./addons,./custom_addons/tops`
  - Such as: `./odoo-bin --addons-path=./addons,./custom_addons/tops -u tops -d odoo18_tops_0.1.1.1`
- In Odoo, go to the `Apps` section in the app switcher (top-left button)
- Click `Update Apps List` on the top bar
- Search for the add-on `Taler-Odoo Payment System`
- Click on the add-on, and press `Activate` or `Install` to complete this step 

> To update the add-on, first update the code using the same way that you first downloaded it, then restart the server and finally click `Upgrade` on the add-on page


### Setup the Taler payment provider

- Once the add-on is installed from the Apps:
  - Go to the payment providers menu. It can be accessed in multiple ways:
    - `Website -> Configuration -> eCommerce -> Payment Providers`.
    - `Invoicing -> Configuration -> Online Payments -> Payment Provider`s.
  - Either way you land here, this is the list of your currently available payment providers.
  - A new `Taler` payment provider will be in this list, set as disabled for now.
  - Click on the Taler payment provider.
  - In the `Credentials` tab, set the Taler merchant URL.
    - By default, the demobank's credentials are used. You can access the demobank [here](https://backend.demo.taler.net/instances/sandbox/)
    - After setting the URL, you can click the `Check URL validity` button to check if the entered URL is reaching a valid Taler merchant, and that this merchant's accepted currencies are compatible with you Taler available currencies.
      - You can find the accepted currencies in the `Configuration` tab.
  - Then set the Taler Merchant Password. It will be used for API calls to the merchant.
  - You may want change the Taler fulfillment message as well. It will be shown on created Taler transactions
    - This change is only for the Taler order, there will be no change in Odoo.
    - If you'd like to change the Odoo fulfillment messages shown to the customers after a payment using Taler, you can do so in the `Messages` tab.
  - The default values are connecting to the sandbox Taler merchant:
    - URL: https://backend.demo.taler.net/instances/sandbox
    - Password: sandbox
  - It is advised, but completely optional, to create a Taler-specific Journal (this can be set in the Configuration tab).
    - This will help during the Accounting process.
  - Click the `Enabled` radio button.
- The initial setup is now complete and Taler payment will be available in all eCommerce, online payments and Invoicing apps.

<img src="README_Pictures/FR/Taler_provider_setting_complete.png" alt="Taler providers settings" width="700px">

### Complete an eCommerce payment using Taler

- Once you have completed the Taler initial setup, customers can pay on your website.
- To do so, they will open the shop and add any items to their cart.
- During the checkout, they can now select the `Taler` payment provider.

<img src="README_Pictures/FR/Taler_ecommerce_checkout.png" alt="Taler eCommerce checkout" width="700px">

- After clicking `Pay now`, a new Taler order will be created on the merchant side, and the customer will be redirected to the Taler order, from which they can pay with any Taler wallet on their phone or web browser.

<img src="README_Pictures/FR/Taler_ecommerce_wallet.png" alt="Taler eCommerce wallet" width="300px">

- On completion of the payment using their wallet, the customer will be redirected back to your Odoo website, which will show a successful payment confirmation.

<img src="README_Pictures/FR/Taler_ecommerce_payment_processed.png" alt="Taler eCommerce payment processor" width="700px">

### Create an invoice that can be paid using Taler

- It is possible to create an invoice that includes a Taler QR Code to pay it.
  - Go to the Invoicing app and create a new invoice.
  - Fill any data relevant to the invoice that you are creating.
  - Important step: In the `Other Info` tab, set the Payment Method to `Taler` (see below). Otherwise, the QR Code will not be generated.
  
<img src="README_Pictures/FR/Taler_invoices_payment_method.png" alt="Taler invoices payment method" width="700px">

- When you are done, click `Confirm` at the top, you will be led to the invoice page.
  - You can now click `Aperçu` to see the Invoice that will be sent to your customer.
  - The invoice's PDF will include a Taler payment QR Code, as well as some Taler order information.

<img src="README_Pictures/FR/Taler_invoices_taler_qr_code.png" alt="Taler invoices taler qr code" width="700px">

- If a customer pays for the invoice using the QR Code present in the PDF, you will have to do a manual payment reconciliation.
  - To do this, once you confirm that you received the payment, go to the Invoices' app page.
  - Click on `Pay`.
  - Confirm the data shown in the opened window, it is recommended to add the Taler OrderID shown on the invoice, to the `Memo` field, to keep track of the payment more easily.
  - Press `Create Payment`.


### Pay an invoice online using Taler

> This process is unrelated to the invoices created with Taler in the previous step\
> Any invoice can be paid online using Taler

- Go to the Invoicing app and create a new invoice.
- Once created, you can press `Preview` to see the page that the customer will see.
- On this page, the user will be able to click `Pay Now`, and choose Taler as a payment option.

<img src="README_Pictures/FR/Taler_invoices_online_payment.png" alt="Taler invoices online payment" width="700px">

- Once they click `Pay`, they will be redirected to the Taler order page, where they can pay with a Taler wallet on their phone or web browser (in the same way as for an eCommerce payment).
- When the payment is complete, the customer will be sent back to the invoice page, with a notice saying that the payment is successful.

<img src="README_Pictures/FR/Taler_invoices_paid_online.png" alt="Taler invoices paid online" width="700px">

### Purchase an Event ticket online using Taler

> Note: to have a fully working ticketing system, you might need to install the python module pycairo:\
> `sudo apt install libcairo2-dev`\
> `pip install rlPyCairo`

- To make event tickets available for customers to pay using Taler:
  - Add the `Events` add-on on your Odoo instance.
  - Go to the settings app, and navigate to the `Events` settings.
  - Tick the `Online Ticketing` setting and save the changes.

<img src="README_Pictures/FR/Taler_ticketing_settings.png" alt="Taler ticketing settings" width="700px">

  - Tickets will now be available to buy using online payments providers, including the Taler payment provider.
  - Customers can navigate the `Events` tab on your website, and choose a ticket to any event they're interested in.

<img src="README_Pictures/FR/Taler_ticketing_events_list.png" alt="Taler ticketing event list" width="700px">

  - Upon clicking an event, they will be asked to provide some identifying information, and then will be lead to a payment page.
  - On this payment page, the customer can select Taler as a payment provider.
  - They will be redirected to a Taler order page, where they can pay using their Taler wallet on the app or web browser.
  - Once the payment is completed, the customer will land back on the odoo page, with their payment successfully processed, and a .pdf of the event tickets available.

<img src="README_Pictures/FR/Taler_ticketing_event_payment_confirmation.png" alt="Taler ticketing event payment confirmation" width="700px">

### Configure Taler payment for point of sale

- Allowing Taler payment on the point-of-sale app requires a few more steps than online payments above.
- Preliminary steps:
  - You need to have previously [setup Taler as a payment provider](#setup-the-taler-payment-provider).
  - Install the `Point of sale` Odoo app.
- Create the Point of Sale payment method:
  - On the top bar, press `Configuration -> Payment Methods`.
  - Create a new Payment Method.
    - Name it `Taler` (You can call it something else, but `Taler` is easier to keep track of).
    - Check the `Online Payment` checkbox.
    - Select `Taler` in the `Allowed Providers` field.
- Add Taler to the point of sale:
  - Make sure that the point of sale register is closed for this step.
  - On the top bar, press `Configuration -> Point of Sales`, you will be redirected to the point of sale list.
  - Select the point of sale you'd like to add Taler payment to.
  - Click on `More settings: Configurations > Settings`, which will lead you to the point of sale's settings page.
    - Alternatively, you can access this page by going to Settings through the app switcher (top-left button), then going to `Point of Sale` section, and selecting the point of sale that you would like to modify.
  - In `Payment -> Payment Methods`, add the payment method you just created (generally `Taler`).
- The setup is now complete, and you can select this new payment provider when a customer pay for an order on the Point of sale that you added the payment method to.

### Pay using Taler on a Point of Sale

- Open a register on one of the Points of Sale for which you have activated the Taler payment method.
- Add any items to the order and click `Payment` at the bottom of the page.
- Select the payment method `Taler` payment method.

<img src="README_Pictures/FR/Taler_pos_taler_payment.png" alt="Taler pos taler payment" width="700px">

- Click `Validate`, it will show a QR Code.
- Scanning this QR Code will redirect to an Odoo page, where the customer will be able to pay with Taler.
- This will bring the customer to a Taler order page, and they will be able to pay using their Taler wallet or web browser.
- Upon payment completion, the customer will be redirected to Odoo, with a confirmation of payment (first picture), and the order on the point of sale's side will show a successful payment, and produce the receipt (second picture).

<img src="README_Pictures/FR/Taler_pos_payment_complete.png" alt="Taler pos payment complete" width="700px">

<img src="README_Pictures/FR/Taler_pos_receipt.png" alt="Taler pos receipt" width="700px">

### Refund an online payment made using Taler

- To make a refund to a payment made using Taler, you first have to find the payment you wish to refund.
- In the `website` or `invoicing` add-on, navigate to `Configuration -> Payment Transactions` on the top bar.
  - This page will show you all the transactions that have been completed.
- Click the transaction that you would like to refund.
  - In the picture below, the transaction to refund is `S00041-3`.

<img src="README_Pictures/FR/Taler_refund_list_of_transactions.png" alt="Taler list of transactions" width="700px">

- On the transaction page, click on the linked payment found in `Payment`.
  - In the picture below, the linked payment is `PBNK1/2026/00001`.

<img src="README_Pictures/FR/Taler_refund_transaction.png" alt="Taler transaction page" width="700px">

- On the payment page, click `Remboursement` in the action button section (top-left) and confirm the refund.

<img src="README_Pictures/FR/Taler_refund_payment.png" alt="Taler payment page" width="700px">

- Confirming the refund will create a new transaction, that you can view in the list of transactions, with the name `R-{Odoo reference number}`.
  - An email containing the refund QR Code will also be sent to the customer's email address.
    - You can view this email in the list of sent emails, found in `Settings app -> Technical -> Emails`
  - To receive the refund, the customer will have to scan the QR Code with their Taler wallet.

<img src="README_Pictures/FR/Taler_refund_email.png" alt="Taler refund email to customer" width="700px">

_Notes:_
  - _You need a functional email sender for this feature to work properly._
    - _Without an email sender, the email will be generated and can be read, but it will not be sent._ 
  - _You can only do full refunds using Taler. Partial refunds are not implemented._

### Test the add-on using the merchant test mode

- The merchant test mode allows you to test the installation of the module, and confirm that the selected merchant are working properly.
- <strong>Warning:</strong> Do not use this mode in production or with published items for sale.
  - _Note: You can decide to keep the payment provider `Unpublished` when using Test Mode, or to `Publish` it by clicking the button at the top of the page. If a payment provider is unpublished only an administrator users will be able to see and use the payment provider. It is advised to keep the payment provider unpublished when using the Test Mode._
  - _Second note: In the Odoo UI, the payment information will be shown with actual values (amount, currency, etc), but the currency will automatically be swapped to `Kudos` right before sending the order to the Taler merchant._

- Here is an example of the flow for this feature:
  - On the payment provider's page, check the `Test Mode` radio button.

<img src="README_Pictures/FR/Taler_test_mode_radio_button.png" alt="Taler test mode radio button selected" width="700px">

- Start the process for any online payment, I will show the process for an eCommerce payment.
  - Navigate to the shop page.
  - Select any product that you'd like to buy as a test, go to your cart and start the checkout process.
  - Once you confirm your order, the Taler payment method will appear, with some icons.

<img src="README_Pictures/FR/Taler_test_mode_payment_method_with_icons.png" alt="Taler test mode payment method with two icons, striked-through eye and yellow warning sign" width="700px">

- Explanation of the icons:
  - The red striked-through eye means `Unpublished`. It is there to let you know that this payment method is not visible to visitors, only users that have administrator access rights to the shop will be able to see the test mode Taler payment provider.
  - The yellow warning sign means `Test mode`. It is there to warn you that the test mode is activated for this payment method.
- Pay the order. A corresponding order will be created on the Taler merchant, with a currency change.
  - The currency originally used will be swapped with `Kudos`.
    - Kudos is an imaginary currency created for Taler. It can be used for free to test transactions with your Taler wallet.
- A Taler order will be created, you can open it and pay with your wallet. (Notice that the currency is replaced with Kudos.)

<img src="README_Pictures/FR/Taler_test_mode_taler_order_payment.png" alt="Taler test mode payment on Taler, showing kudos currency" width="700px">

- Once the order is paid using the imaginary currency, you will be sent back to the completed Odoo order.

<img src="README_Pictures/FR/Taler_test_mode_taler_payment_completed.png" alt="Taler test mode payment shown as completed on Odoo website" width="700px">

- Once this step is done, the test is complete. The add-on works and the Taler merchant endpoint can receive your orders for compatible currencies.

---

### Change settings using CLI

- To change Odoo settings using CLI, run the Odoo CLI shell by adding `shell` to your original command line to start Odoo.
  - Such as `./odoo-bin shell --addons-path=./addons,{custom_addons_path}/tops -u payment_taler -d odoo18_tops_0.1.1.1`
- Run these commands to edit the settings. You can use `get_params` to print the current value, and `set_params` to set a new value:
  - `env['ir.config_parameter'].set_param('payment_taler.taler_merchant_url', 'https://backend.demo.taler.net/instances/sandbox/')`
  - `env['ir.config_parameter'].set_param('payment_taler.taler_merchant_password', 'sandbox')`
- <strong>WARNING:</strong> You need to commit the changes to the database before closing the shell instance and restarting Odoo:
  - `env.cr.commit()`
  - `exit()`

---

### Editing rights to the payment provider settings

- As with other payment providers, Odoo users will have limited access to the Taler payment provider settings.
- Only user that belong in the `base.group_system` user group will be able to access and modify the Taler payment provider settings.

---

### Uninstall the add-on

- To uninstall the add-on, you have to go to the `Apps` app on Odoo.
- Search for, and go to the `Taler-Odoo Payment System` add-on.
- Click `Uninstall`, the add-on should be uninstalled.
  - _Note: If you have made any transactions using Taler with this add-on, you will not be able to uninstall it._
- You can reinstall the add-on at a later time.
- If you added a payment method record for the point of sale app: ([see the related section](#configure-taler-payment-for-point-of-sale)):
  - Go to the `Point of Sale` app, and navigate to `Configuration/Payment Methods`.
  - Click on the `Taler` record you created when setting up the point of sale payment system, it should be highlighted in red because the payment provider is not available anymore.
  - Click on the gear at the top, and then either `Archive` (better for data conservation) or `Delete` (more risky because you might lose track of some payments)
  - On the top bar, go to `Configuration -> Point of Sales`.
  - Select a point of sale that you made Taler payments available for.
  - Click on `More settings: Configurations > Settings`, which will lead you to the point of sale's settings page.
  - In Payment -> Payment Methods, remove the Taler payment method.
    - Do this step for every point of sale you made Taler payments available for.

---

## Folder structure

This add-on uses a quite standard folder structure:
- `controllers` contains the controllers used by the add-on.
- `data` contains setup data that is processed when someone installs the add-on, as well as email templates.
- `i18n` contains the data for localization and translation.
- `models` contains the Odoo models. There are 4 models:
  - `taler_api_method`, which contains the methods used to communicate to the Taler merchant API.
  - `taler_invoicing`, which contains the methods used when creating invoices with Taler.
  - `taler_provider`, which contains the methods used by the Taler payment provider.
  - `taler_transaction`, which contains the methods used to complete a transaction with Taler.
- `README_Pictures` contains all the pictures shown in this README.
- `security` contains the (unused) `ir.moder.access.csv` file to manage access rights.
- `static` contains logo data and other image assets for the add-on.
- `tests` contains unit tests for this project.
- `utils` contains utility methods (such as logging).
- `views` contains the views used for the models.

---

## Run unit tests

- To run unit tests on a new db, use this command:
  - `./odoo-bin --addons-path=./addons,{custom_addons_path}/tops --test-enable -d test_db_2 -i payment_taler --stop-after-init --test-tags taler`
    - The db name after -d is arbitrary and can be replaced by any other names.
- In the results logs, you should expect to see `odoo.tests.result: 0 failed, 0 error(s) of x tests when loading database`.
  - x is the number of unit tests, currently 11.

---

## Common issues

### The `Check URL validity` button is showing an error

- This button checks that the chosen Taler merchant is valid and supports the same currencies that you are using. If your Taler provider accepts a currency not supported by the Taler merchant, an error will be raised.
  - The error message will show any discrepancies, and the accepted currencies on both sides.
- To change the currencies you'd like to support with Taler, go to the `Configuration` tab in the payment provider, and navigate to `Availability -> Currencies`.
  - This change will be overwritten when you restart the Odoo server.
  - For a more permanent change, you can edit the `const.py` file at the root of this add-on, and comment/uncomment the currencies that you want to set as Taler configuration.
  - `const.py` is loaded at server start, 

_Note: Because KUDOS is an imaginary currency, you will not find it in the list in Odoo._

---

## Translation & Available languages

- This module is currently available in English and French
  - Invoices and emails sent to customer for refund are also translated, and will be sent in the language set on the customer's profile.
  - This README is also translated in the file README_FR (ADD LINK TO THE README_FR.md FILE HERE) 
  - Translation in other languages is welcome, please see [here](#how-to-add-a-translation) for a guide on how to add a translation.

---

## Following the updates of this module:

- You can see updates announcement in this category of the ICH.taler.net forum: https://ich.taler.net/c/integrations/odoo/29
- I also post regular devlogs in this thread of the same forum: https://ich.taler.net/t/taler-odoo-payment-system-devlog/437

---

## How to contribute

- Contributions to the Taler payment integration are always welcome!
- To make a contribution:
  - Fork this repository
  - Clone the fork on your local machine
  - Create a new branch
  - Make your changes
  - Commit your changes
  - Push to your fork
  - Open a pull request on the original TOPS repository


- Some features that may need further development:
  - Add more translations to help make the add-on more accessible (see [here](#how-to-add-a-translation) for a guide on how to add a translation).
  - Implement partial refunds for customers.
  - Update the add-on for Odoo 19.
  - Keep the add-on updated for future Odoo releases.

---

## How to add a translation

- If you would like to add a translation to the module, the process is rather simple:
  - The file `i18n/payment_taler.pot` [available here](https://codeberg.org/Nemael/tops/src/branch/18.0/payment_taler/i18n/payment_taler.pot) is the base translation file, with all the strings of text stored in it.
  - Copy this file's content in a new file `{New language}.po`, such as `fr.po`
  - In this new file, translate all the strings of text that you would like to translate. You can use `fr.po` [available here](https://codeberg.org/Nemael/tops/src/branch/18.0/payment_taler/i18n/fr.po) as a guide on how to format the translation.
  - Once complete, you can re-make your Odoo test database, and change your user's language to the added translation's language. The translation you made should appear on Odoo.
  - If you are encountering any issues, please open a thread in this forum category https://ich.taler.net/c/integrations/odoo/29 (You can ping me as well, @Nemael). Please specify that you are doing a new translation and for which language.

---

## Tech support

If you are encountering any issues with the add-on, please don't hesitate to either:
- Open a thread in this forum category https://ich.taler.net/c/integrations/odoo/29 (You can ping me as well, @Nemael). Please explain your issue in detail.
- Open an issue on the Codeberg repository https://codeberg.org/Nemael/tops/issue. Please explain in details the issue you are encountering.

---

## Special thanks to

- The [Odoo Community Association (OCA)](https://github.com/OCA) and their many Open-Source addons, which helped me find my way around which Odoo flows to work on.
- [petites singularites](https://ps.lesoiseaux.io/taler/) for the administration of the [ICH Forum](https://ich.taler.net/), where I could post questions and updates about my progress, and get support from the community.
- The [Kashier](https://github.com/Kashier-payments/Kashier-Odoo-Payment-Add-on) and [Sadad](https://github.com/Adnanghanchi/Odoo-Payment-Provider) payment providers integrations in Odoo, which provided payment integration examples that helped me steer my work in the right direction.
- Codeberg user @jans for their QA and their help to standardize my code. 

---

## Funding

This project is funded through [NGI TALER Fund](https://nlnet.nl/taler), a fund established by [NLnet](https://nlnet.nl) with financial support from the European Commission's [Next Generation Internet](https://ngi.eu) program. More information at the [NLnet project page](https://nlnet.nl/project/TALER-Odoo-module).

[<img src="https://nlnet.nl/logo/banner.png" alt="NLnet foundation logo" width="20%" />](https://nlnet.nl) 

---

## Licensing

[![REUSE status](https://api.reuse.software/badge/codeberg.org/Nemael/tops)](https://api.reuse.software/info/codeberg.org/Nemael/tops)

This work is published under license [LGPL-3.0-or-later](./LICENSES/LGPL-3.0-or-later), and the devlog is published under license [CC0-1.0](./LICENSES/CC0-1.0.txt). You can find license information at the top of each file.
