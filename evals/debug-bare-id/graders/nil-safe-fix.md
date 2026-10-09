---
type: regex
pattern: "customer&\\.name|customer\\.nil\\?|customer\\.present\\?|customer\\.blank\\?|try\\(:name\\)|if customer|unless customer|return .* unless customer"
target: last_message
---
The answer contains a nil-safe fix for the customer lookup.
