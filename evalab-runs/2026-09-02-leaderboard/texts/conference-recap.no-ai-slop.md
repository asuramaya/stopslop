Five of us went to SREcon EMEA in Dublin last week. We split the schedule so nobody sat in the same room twice, then compared notes over dinner.

Three of the four platform teams we talked to have stopped running their own Kafka. Two moved to a managed service. One replaced it with Postgres queues and dropped the broker bill to zero. When we asked about volume, nobody was pushing more than 40 MB/s. Neither are we. We had a self-hosted Kafka upgrade penciled in for Q4, and that plan is now a question.

Priya sat in on two incident-review talks. Both teams had thrown out the five-whys template and replaced it with a plain narrative: what we saw, when we saw it, what we tried, what we still don't know. Their write-ups got longer and their action-item lists got shorter, from about a dozen per incident down to two or three that actually shipped. We're running that format on the next Sev2 and comparing.

The vendor floor was thinner than last year. Six of the eleven observability booths opened with an agent demo, and four of those were the same underlying product with different logos. We asked each of them what happens when the agent misreads a trace at 3 a.m. and pages the wrong team. Nobody had an answer past "you can review the suggestions."

Three things we're doing this month: benchmark Postgres queues against our real traffic, rewrite the postmortem template before the next incident, and skip the vendor evaluations we scheduled in August. Matteo is writing up the queue benchmark; ping him if you want in.
