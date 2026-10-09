---
type: llm
---
PASS if the final answer works on fault 5001 (NoMethodError, undefined method 'name' for nil, in Order#customer_name) as the most recent error and proposes a diff that handles an order without a customer.
FAIL if it works on a different fault (such as the Faraday::TimeoutError, 5002) or gives no diff.
