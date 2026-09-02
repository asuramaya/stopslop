## Observability is how you find out what you shipped

Every team has a version of the same story. A deploy goes out on a Thursday afternoon, the dashboards stay green, and then on Monday someone in support forwards a customer email about checkout failing "sometimes." Nobody can reproduce it. The logs have the request IDs but not the account tier, the traces stop at the API gateway, and three engineers spend two days rebuilding, from fragments, a picture of a system they wrote themselves.

That gap between what you deployed and what you can see is where most incident time actually goes. Google's 2023 DORA report found that elite performers restore service in under an hour while low performers take more than a week. The code isn't a thousand times better.

The difference is how fast you can answer a question you didn't anticipate asking. At 2am, with a customer waiting and no local repro, using only the telemetry your past self decided to keep. Monitoring covers the questions you wrote down in advance: is CPU above 80 percent, is the error rate over threshold, is the queue backing up. Observability is the other half — enough detail in your telemetry to slice by customer, region, feature flag, and client version after the fact, without shipping new instrumentation first and waiting a release cycle to find out whether it helped.

The practical test is simple. Someone reports the app is slow for one enterprise customer in Frankfurt. Can you confirm or refute that in ten minutes? If not, you have a visibility problem, and it gets more expensive as the system grows.
