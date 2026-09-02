Splitting a 400,000-line Rails monolith into services took us two years, and the first eight months were wasted.

This talk is the account of what we got wrong. We started by drawing service boundaries on a whiteboard from the org chart, extracted three services along those lines, and ended up with a distributed system that shared a Postgres instance and deadlocked under load. Rolling back cost a quarter.

The second attempt started from data ownership instead. We instrumented every query in production for six weeks and built a table-to-endpoint access map, then let the clusters in that map tell us where the seams already were. Two matched the whiteboard. Four did not.

I will walk through the access map and how we produced it, the strangler-fig sequence we used to move traffic without a freeze window, and the three cases where we decided to leave code in the monolith permanently because the extraction cost exceeded any benefit we could measure. The talk includes p99 latency before and after, on-call page volume by quarter, and the infrastructure bill, which went up 40 percent and stayed there.

For engineers and tech leads who have been handed this migration and want to know which parts are avoidable.
