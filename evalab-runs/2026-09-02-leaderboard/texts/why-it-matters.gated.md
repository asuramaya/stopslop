# Nobody Reads the Dashboards Until 3 a.m.

Checkout starts failing at 2:47 a.m. Not all of it — about one request in forty, and only for customers whose cart holds a gift card. Your alert watches overall error rate, so it stays quiet through the night. Support picks up the first three tickets a little after nine, once the East Coast is awake. By the time an engineer opens a terminal, the interesting evidence is gone: the pod that was misbehaving got recycled at four, and its logs rotated out an hour later. What's left is an aggregate graph with a bump in it that could be anything.

Plus a Slack thread where four people take turns guessing.

That gap is what observability is actually about. Not dashboards. A dashboard is the souvenir you keep after you already know the answer. The real question is whether your system can answer something nobody thought to ask in advance, at 3 a.m., with the logs already gone.

Monitoring assumes you know your failure modes.

You pick the metrics, set thresholds, and get paged when a number crosses a line. That works for the outages you have already had. It does nothing for the gift-card path, because nobody writes an alert for a condition nobody imagined.

So the payoff is not fewer incidents. Teams that get this right have roughly as many as everyone else. Their incidents are just shorter, and they spend the time fixing the thing instead of arguing about which service broke.
