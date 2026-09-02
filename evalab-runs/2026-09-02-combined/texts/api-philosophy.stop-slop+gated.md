Design Philosophy

We built this API so you can guess the third endpoint after you have used two. Resources take plural nouns, and collections accept the same filter and cursor parameters. A field named `created_at` holds an RFC 3339 timestamp in `/orders`, and it holds one in `/refunds` too. We return errors you can act on: a 422 names the field that failed and the rule it broke, so your code can point the customer at the line to fix instead of showing a generic message.

We never bury a failure in a 200.

We version at the account level and date the versions. You pin `2026-01-15`, and we hold that response shape until you move. We add new fields to your current version. Before we remove one, we email you and wait twelve months.

We would rather ship a small surface we can keep than a wide one we cannot. We left out batch writes, and we left out server-side aggregation. Two engineers maintain this API, and we turned both features down because a promise we break costs you more than a feature we skip.

If you need one of them, tell us what you are building and we will tell you where it sits in the queue.
