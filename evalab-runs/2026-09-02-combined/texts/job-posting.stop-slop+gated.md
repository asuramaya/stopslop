**Senior Backend Engineer**

Meridian Payments · Chicago or US-remote · $185k–$215k + equity

We move money for 3,000 marketplaces. Last quarter we settled $4.1B across 14 currencies, and our ledger service handled the peak day at 9,000 writes per second.

You would own that ledger. The team is four engineers and one product manager. Ana, our staff engineer, has been rewriting the reconciliation path in Go for two quarters, and she needs a second person who can hold the whole double-entry model in their head.

The work starts with our Postgres ledger, which our projections put eleven months from its write ceiling. You would design the sharding plan before we get there. You would also cut settlement latency for our two largest partners, who currently wait 40 minutes for a payout confirmation. Expect to spend about a third of your time on incident review and partner debugging. Payments break in specific ways, and we read the logs together.

We want six or more years writing backend services that other teams depend on, plus Go or Java in production. Your Postgres knowledge should run to query plans, lock contention, and migrations against live traffic. If you have shipped an idempotency layer or fought a duplicate-charge bug at 2am, say so in your note.

We do not ask for take-home projects. You will pair with Ana for two hours on our real reconciliation code, then talk with our VP of Engineering about how you have handled a bad deploy.

Email ana@meridianpay.com with your resume and one paragraph about a system you rebuilt.
