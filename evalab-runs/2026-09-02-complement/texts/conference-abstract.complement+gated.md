Cutting the Monolith Without Cutting the Release Train

Our billing platform ran as a single Rails application for nine years: 400,000 lines, a 90-minute test suite, and a deploy process that required two engineers and a rollback plan. Splitting it took eighteen months, and we kept shipping features the whole time.

This talk covers what actually happened. I'll walk through how we picked the first three services (invoicing, tax calculation, payment retries), and why we chose those over the ones that looked easier.

Then the strangler-fig setup we used to route traffic gradually while the old code kept running behind it. I'll show the schema-splitting work in detail, since that consumed roughly half the total effort and none of our original estimate. You'll also hear about the parts that went badly: we built a shared library for cross-service auth that became its own coupling problem, we spent four months on a service mesh before admitting our traffic volume didn't justify it, and two of the services have since been merged back into the monolith they came from.

If you're weighing a decomposition against staying put, you'll leave with a clearer sense of the real cost, plus a list of questions to answer before you write the first new service.
