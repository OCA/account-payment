-- disable easypay payment provider
UPDATE payment_provider
   SET state = 'test',
       easypay_account_id = '2b0f63e2-9fb5-4e52-aca0-b4bf0339bbe6',
       easypay_api_key = 'eae4aa59-8e5b-4ec2-887d-b02768481a92'
 WHERE code = 'easypay' and state != 'test';
