# API client library 2.0

We shipped 2.0 today. It changes how the client authenticates, how it retries failed requests, and how it reports errors, and none of those changes are backward compatible with 1.x.

The old client handled auth with a single API key baked into the constructor. That worked for one service talking to one account, but broke down the moment someone needed to rotate keys or support multiple accounts in the same process. 2.0 replaces it with a credential provider interface: pass a static key if that's all you need, or pass a function that returns a fresh token on each call.

Retries used to be a fixed three attempts with a flat one-second delay, regardless of what failed. Now the client distinguishes between a rate limit, a timeout, and a server error, and backs off differently for each. A 429 response respects the `Retry-After` header if the server sends one. A connection timeout retries twice; a 500 retries once.

Error objects changed shape. In 1.x, every failure raised the same `ClientError` with a string message. In 2.0, errors subclass by cause: `AuthError`, `RateLimitError`, `ValidationError`. Code that catches `ClientError` broadly still works, since the new classes inherit from it, but code that parsed the message string to figure out what went wrong needs to switch to `isinstance` checks.

The migration guide covers all three changes with before-and-after code. Install with `pip install client==2.0.0`, or pin to `1.x` if you're not ready to move yet — we'll keep patching that branch for six months.
