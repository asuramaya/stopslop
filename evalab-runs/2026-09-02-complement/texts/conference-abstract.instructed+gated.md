# Breaking up the monolith without breaking the company

Three years ago our billing platform was 400,000 lines of Ruby in one deployable unit. A single slow query in report generation could take down checkout. Deploys took 90 minutes and happened on Thursdays, because nobody wanted to spend a weekend rolling back.

We now run 14 services. Getting there took 20 months, cost us two production incidents worth writing about, and taught us that most of the advice on this topic assumes a greenfield you do not have.

This talk covers what we did in order: how we found seams in code that had none, why we extracted the payment ledger first even though it was the scariest piece, and how the strangler-fig pattern behaves when the thing you are strangling is still shipping features every week. I will show the actual dependency graphs at month 0, month 8, and today.

I will also cover what went wrong. We split one service along the wrong boundary and spent four months merging it back. Our test suite runtime went up before it went down. On-call got worse for a full quarter.

If you are staring at a monolith and a mandate, you will leave with a sequence you can argue for on Monday.
