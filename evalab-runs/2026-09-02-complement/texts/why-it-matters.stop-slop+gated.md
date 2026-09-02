Your checkout service starts returning 500s at 2:14 in the morning. The pager wakes Priya. She opens the dashboard your team built last quarter and finds CPU at 40 percent, memory flat, error rate climbing past 12 percent. None of those graphs name the failing dependency. So she starts guessing. She restarts the payments pod, watches, restarts the session cache, watches. At 3:40 she notices a config change someone shipped Friday afternoon that pointed a retry loop at a deprecated auth endpoint. Ninety minutes of revenue gone, and most of it went to guessing.

Monitoring told Priya the system was sick. It could not tell her why, because your team decided in advance which questions the dashboards would answer. Your team picked three questions months before this outage existed, and CPU, memory, and error rate were all of them.

Observability changes what Priya can ask at 2:14am. When your services emit structured events with the request ID, the customer ID, the downstream host, and the retry count attached, she queries her way to the auth endpoint in four minutes instead of ninety. She asks a question nobody predicted and gets an answer.

The gap costs more than sleep. Google's SRE teams measure it as time to detect plus time to diagnose, and diagnosis dominates the number in most incidents I have seen. Teams pour money into faster alerting and leave the expensive half alone.

This post covers what to instrument first, how to structure events so they stay queryable at volume, and what to do about the cardinality bill that arrives once you start adding customer IDs to everything.
