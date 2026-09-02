At 2:14 on a Tuesday morning our checkout API started returning 500s to roughly one request in nine. We had dashboards. Four of them, all green. CPU fine, memory fine, request rate normal, error budget showing a tidy burn line that hadn't moved all week. It took until 6:40 to work out that a Redis client in one pod had quietly fallen back to a stale connection pool after a failover, and it only broke for users whose session keys hashed into one slot range.

Nobody had a dashboard for that. Nobody could have.

Monitoring answers questions you thought to ask in advance. Pick the metric, pick the threshold, get paged when the number crosses it. That works fine for disk space. It does nothing for the failure you've never seen before, which, once your system is more than two or three services deep, is most of them.

So here's the test I use. Can you take a question you've never asked, about one user you can name, in a five minute window from six hours ago, and answer it without shipping new code? If not, you're monitoring. You aren't observing.

And I want to be blunt about the price, because most posts on this subject skip straight past it. Doing observability properly means high cardinality data. High cardinality means storage bills, sampling decisions, and an uncomfortable conversation with whoever owns your infra budget. It means going back to instrument code that currently works and isn't bothering anyone. Teams defer it for exactly that reason. Then they spend four and a half hours at 2am chasing a hash slot.
