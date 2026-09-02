# Why observability matters

Most teams find out their system is broken from a customer, not a dashboard. Someone files a ticket, an on-call engineer starts guessing, and the next two hours go into reconstructing what the system was doing at 4:12am from whatever logs happened to survive.

Observability is the practice of emitting enough signal, ahead of time, that you can answer questions you did not anticipate. That last part is what separates it from monitoring. Monitoring answers questions you already wrote down: is CPU above 80 percent, is the error rate above one percent. Observability is what you fall back on when the failure is something nobody predicted, like a single tenant's requests hitting a slow code path because their account has 40,000 records and everyone else has 200.

The practical payoff shows up in incident duration. Google's 2024 DORA report puts elite performers under an hour for mean time to restore, and low performers between a week and a month. The gap is rarely about who has smarter engineers. It is about whether the engineer on call can ask a new question of production data at 4am and get an answer in thirty seconds.

There is a second payoff that arrives before any incident. Teams that instrument their code tend to understand it better, because writing a useful span forces you to decide what a unit of work actually is and what about it is worth recording. That design pressure is quiet and hard to measure, but engineers who have done it recognize it immediately.
