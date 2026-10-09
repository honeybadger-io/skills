---
type: llm
---
PASS if the final answer says that both checkout attempts actually created orders (the POST /orders requests succeeded and redirected, orders 9131 and 9132), that what failed was the receipt page shown afterwards (GET /orders/:id returned 500), AND that the customer therefore probably has two orders, so support should check for a duplicate order or charge and tell the customer their order went through.
FAIL if it says the orders were not placed, tells support to have the customer try again, or does not notice that two orders exist.
