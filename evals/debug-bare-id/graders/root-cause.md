---
type: llm
---
Judge only the root cause and the fix. Ignore extra notes, caveats, or side observations in the answer.

PASS if both are true:
1. The answer says fault 5001 happens because guest orders have no customer (customer is nil), so `customer.name` in `Order#customer_name` raises.
2. The answer proposes a code change that handles an order without a customer.

FAIL if the answer names a different cause, or proposes no code change for a missing customer.
