## You already have monitoring. That's the problem.

At 2:14 on a Tuesday morning the pager goes off: checkout latency above threshold. You open the dashboard. Latency is, in fact, above threshold. Congratulations, you now know exactly as much as the alert already told you. So you start guessing. Restart the payment service. Nothing. Roll back the afternoon's deploy, which touched a template file and cannot plausibly be the cause, because rolling back is the only move you have. Forty minutes later somebody notices that a third-party address-validation API is timing out for customers whose postal codes contain a space, which is to say everyone in Canada and the UK.

Those forty minutes were not a skill gap.

Your engineers are good. The system simply could not answer a question nobody had thought to ask in advance. That is the line between monitoring and observability: monitoring answers the questions you wrote down last quarter, while observability lets you interrogate a running system about failures you have never seen before, at 2 a.m., without shipping new code first.

It matters more now because the systems got stranger. A monolith and a database had maybe a dozen failure modes worth planning for. Forty services, three managed queues, a CDN and somebody else's API fail in combinations, and combinations are not enumerable. No dashboard gets you out of that. You can only build a system you are able to ask questions of.

Here is what that takes.
