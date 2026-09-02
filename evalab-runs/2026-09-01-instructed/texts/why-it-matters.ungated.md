**Your dashboards are green. The customer is on the phone.**

Every team that ships anything has lived this one. CPU normal, memory normal, every pod healthy, and somebody in São Paulo still can't finish checkout. The graphs on the wall answer a question you thought to ask nine months ago, when you built them. About the question you have right now, at 2 a.m., they have nothing to say.

That gap is the whole argument for observability. Monitoring covers the failures you predicted: disk fills, queue backs up, error rate crosses a line, page goes out. It's a fixed set of questions, decided in advance. Observability is the ability to ask a question you've never asked before — split p99 latency by build ID, then by region, then by the eleven customers on the new pricing tier — and get an answer from data already on disk, without deploying anything.

The difference stops being philosophical the first time you're in an incident. A team with metrics alone starts guessing: roll back the deploy, restart the service, check if it's DNS. A team with wide events and traces reads the shape of the failure off the data. One retries until something works. The other knows.

Distributed systems made this non-negotiable. When a request touches fourteen services, "which one is slow" isn't answerable by staring at fourteen dashboards. You need the request itself to carry its story.

So the question for your team isn't whether to instrument. It's how many outages you're willing to debug by guessing first.
