---
type: llm
---
PASS if the final answer links the customer's errors to the NoMethodError fault (5001) and explains the cause: guest orders have no customer, so `Order#customer_name` (app/models/order.rb) calls `name` on nil when the receipt page renders.
FAIL if it blames something else, or names the error without explaining why guest orders hit it.
