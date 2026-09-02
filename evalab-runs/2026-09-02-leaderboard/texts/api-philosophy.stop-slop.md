# Design Philosophy

We built this API around a small number of nouns. Accounts, transfers, and ledgers. If you understand those three, you can predict the shape of an endpoint you have never called.

Every response carries the full object, not a pointer to it. You will send more bytes over the wire. In exchange, you skip the second round trip and the cache invalidation logic that comes with it. We made that trade on purpose after watching support tickets pile up from partial payloads.

Errors return machine-readable codes alongside human sentences. Parse the code. Read the sentence when something breaks at 3am and you need to know which field you sent wrong.

We version at the account level, not the URL. When you upgrade, you upgrade your whole integration on a date you pick from the dashboard. Nobody at our company flips that switch for you.

Idempotency keys are required on writes. We rejected the optional-key design because the teams who most need retry safety are the ones who forget to opt in.

We remove things slowly. A deprecated field keeps working for eighteen months, and we email the address on your account twice before it stops. Read the changelog if you want the earlier warning.
