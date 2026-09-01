## Nobody Knows Why Checkout Got Slow

Your p99 on `/checkout` went from 180 ms to four seconds sometime between Tuesday and Friday. That much you can see on the latency graph. Everything after that is guesswork.

So the team starts the ritual. Someone scrolls Grafana looking for a spike that lines up. Someone else pulls the deploy log and finds eleven releases in that window, any of which could be it. A third person opens the database dashboard, sees connection counts that look vaguely high, and says "maybe it's the pool?" — and now three engineers spend a day chasing a hypothesis that nobody can confirm or kill, because the data to settle it was never collected in the first place.

That's the actual cost. Not the outage. The hours your best people spend reconstructing what the system was doing, from evidence that wasn't designed to answer questions.

Monitoring tells you a thing broke. You picked the metric in advance, you set the threshold in advance, and the alert fires when the number crosses it. That works fine for the failures you predicted. It does nothing for the ones you didn't, which is most of them, because distributed systems fail in combinations nobody wrote a dashboard for.

Observability is the other move. You instrument richly enough that you can ask a question you never anticipated and get an answer in minutes. Which customer. Which shard. Which code path. Not "is it broken" but "what exactly is it doing right now."
