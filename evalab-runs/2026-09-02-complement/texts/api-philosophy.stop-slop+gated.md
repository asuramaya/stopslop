# Design Philosophy

We built this API around one assumption: you will read the docs once, then work from memory. So we made it memorable.

Every endpoint takes and returns JSON. Every collection paginates with the same two parameters. Every error carries an HTTP status you already know and a machine-readable `code` you can switch on, so learn one resource and you have learned all of them.

We prefer explicit parameters over clever defaults. If a request depends on a value, you pass that value. We will not guess your timezone, your currency, or which of your three workspaces you meant. That refusal costs you a few keystrokes per call and saves you the class of bug where a report comes back correct in staging and eight hours off in production.

Nothing here breaks under you. When we change behavior, we ship a new dated version and keep the old one running. You upgrade by changing a header, on your schedule, after reading a migration note that lists what moved and where it went. Inside a version we add fields and never remove or repurpose them, so write your clients to ignore keys they do not recognize.

Idempotency keys work on every write.

Retry a timed-out request with the same key and you get the original response back, not a duplicate charge or a second record. When we got something wrong, we say so in the changelog and name the fix.
