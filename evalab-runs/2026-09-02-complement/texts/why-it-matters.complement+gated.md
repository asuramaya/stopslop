Your service went down at 2:14 on a Tuesday morning. The on-call engineer got paged, opened the dashboard, and saw that CPU was fine, memory was fine, and error rates were flat. Meanwhile, checkout was failing for about eleven percent of users in one region. It took forty minutes to find the cause: a third-party address-validation call that had started timing out, swallowed by a retry loop that never logged anything.

That gap between "the system is broken" and "here is what broke" is the thing observability closes. Monitoring tells you a threshold was crossed. Observability lets you ask a question you did not think to ask in advance, and get an answer from data you already collected. The distinction sounds academic until you are the one at 2:14 guessing.

For engineering teams, the payoff shows up in three places. Incidents get shorter, because the first twenty minutes go to reading traces instead of forming hypotheses. Changes get safer, because you can watch a deploy affect real request latency for real users rather than waiting for complaints. And the code itself gets better, since instrumenting a service forces you to articulate what it is supposed to do and what counts as a failure.

None of this comes free. Good telemetry costs storage, engineering time, and a fair amount of arguing about what to name things. Teams that treat it as a checkbox end up with dashboards nobody reads and a bill nobody can explain.

This post covers what to instrument first, how to keep the cost bounded, and what to do when your traces still don't answer the question.
