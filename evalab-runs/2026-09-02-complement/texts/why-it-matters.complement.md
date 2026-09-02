Every engineering team has a version of the same bad night. A customer writes in to say checkout is broken. Nobody can reproduce it. The dashboard is green, the error rate looks normal, and four people spend three hours reading logs in three different tools before someone notices that a single downstream service started returning 200s with empty bodies.

That night is expensive, and it repeats. The cost is not really the three hours. It's that the team learns to distrust its own instruments, and once that happens people stop looking at them at all.

Observability is the practice of building systems you can ask new questions about after they're already running. Monitoring answers the questions you thought to ask in advance: is the disk full, is the queue backed up, did the health check fail. Those questions are useful right up until the moment your outage doesn't match any of them, which is most of the time in a system with more than a handful of services.

The difference shows up in what you can do at 2 a.m. With good monitoring, you know something is wrong. With good observability, you can narrow it down to the specific customer, the specific request path, and the specific version of the specific service that started behaving differently forty minutes ago, without deploying new code to find out.

For most teams, the gap between those two positions is measured in hours of downtime per incident and in how many engineers get pulled in to close it. That's the case this post is going to make concrete.
