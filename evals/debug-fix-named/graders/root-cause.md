---
type: llm
---
PASS if the final answer says the error happens because guest orders have no customer (customer is nil), so `customer.name` in `Order#customer_name` (app/models/order.rb) fails, AND it shows a diff that handles a missing customer (for example `customer&.name` with a fallback), AND it adds or proposes a test for an order without a customer.
FAIL if it blames something else, gives no diff, or the diff does not handle a nil customer.
