We split a 400,000-line Rails monolith into 31 services over two years. Roughly half of those splits paid off.

This talk walks through what we did, in order, with the numbers. Deploys went from one a day to about forty. Checkout p99 latency got worse for eight months before it got better, because every extracted service added a network hop we had not budgeted for. Two services went back into the monolith in year two, and I'll explain what made those two different from the ones that stayed out.

Most of the time goes to the parts that are hard to look up: how we picked cut lines by following transaction boundaries, how we ran the strangler pattern against a database nobody was willing to shard, and what on-call looked like at month six, when a single failed order touched nine services and no one could say which one dropped it.

You'll leave with the checklist we now run before extracting anything, and a rough cost in engineer-months per service.

For engineers and tech leads weighing a similar split. Some Rails and Postgres background helps, though the failure modes are the same in any stack.
