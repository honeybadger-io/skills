---
type: llm
---
PASS if the final answer (1) says the customer's address updates were rejected (status 422, several attempts from Oct 5 to Oct 7) and their address was not saved; (2) gives the cause: the postal code check added in the "Validate postal codes on saved addresses" commit (app/models/address.rb) only accepts US ZIP-style five-digit codes and ignores country, so their UK postcode fails; (3) says other customers whose postal codes are not in that format (such as UK, Canadian, or Australian ones) have failed the same way since the Oct 4 deploy, as a pattern across customers rather than one account; AND (4) proposes a fix (accept other countries' postal code formats, for example by validating per country) and what to tell the customer.
FAIL if it says nothing was found or that the problem is on the customer's side, blames an exception or a fault, or does not connect the failures to the postal code validation.
