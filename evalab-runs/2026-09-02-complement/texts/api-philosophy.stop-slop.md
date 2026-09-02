Design Philosophy

We built this API for people who read the reference once and then write code from memory. Every endpoint takes the same shape, so you can guess the next one before you look it up.

Resources are nouns. Verbs live in the HTTP method. POST to /invoices creates an invoice, and GET on the same path lists them. You will not find /createInvoice or /getInvoiceList in this reference.

Every endpoint returns the same error envelope: a stable code your program can branch on, plus a sentence you can show a customer.

We version at the URL root and keep old versions running for eighteen months after we announce a replacement. Your integration keeps working while you schedule the upgrade.

Defaults favor the common case. Pagination starts at fifty records. Timestamps come back in UTC, formatted as ISO 8601. Currency amounts arrive as integers in the smallest unit, so your ledger and ours agree to the cent.

We answer requests we can answer in one round trip. If a call needs a second lookup to be useful, we treat that as a bug in the design and fix the response, not the guide.

When someone proposes a feature, we ask whether it earns another page here. Most proposals do not, and we close them.
