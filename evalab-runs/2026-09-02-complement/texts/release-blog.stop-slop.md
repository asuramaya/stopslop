# apiclient 2.0

We shipped 2.0 today. The rewrite took four months, and it breaks things you depend on, so read this before you upgrade.

The old client opened a connection per request and dropped it after the response. Under load, you burned through sockets. Rachel on the platform team traced a customer's timeout storm to that behavior in March, and we rebuilt the transport around a pooled connection manager. The same benchmark against our staging cluster handles 4,200 requests per second, where 1.0 topped out near 900.

We removed the callback API. If you wrote `client.fetch(url, cb)`, you write `await client.fetch(url)`. The codemod in `tools/migrate` rewrites most call sites. It missed about one in twelve across our own repos, and the compiler catches the rest.

Retries changed. 1.0 retried any failed request three times, POSTs included, which duplicated orders for two customers we know about. 2.0 retries idempotent methods and gives you `retry: true` when you want the old behavior on a specific call.

Type definitions ship inside the package. Drop `@types/apiclient` from your `package.json`.

We keep the 1.x branch alive until March 2027 and patch security holes there. Nothing else lands on it.

Install with `npm install apiclient@2`. The migration guide walks through each break in the order you will hit it. If the codemod mangles your code, open an issue and paste the before and after. Diego reads that queue each morning and has turned around most reports the same day.
