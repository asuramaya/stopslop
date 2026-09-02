**A Year of Fewer Pages**

We started January with a 4 a.m. incident and ended December with a queue nobody had to babysit. That's the arc.

The big one was the migration off the monolith's job runner. It took five months, three false starts, and one week in June where we quietly rolled everything back and pretended it hadn't happened. It had. But the second attempt held, and p99 enqueue latency went from 2.1s to 180ms. Pages dropped from 31 in Q1 to 6 in Q4.

Some things we got wrong. We built the internal metrics dashboard nobody asked for, and after eight weeks of work it had four regular users, two of whom were on this team. We killed it in September. Lesson filed under "ask first." Rina's on-call handoff doc is now the thing new hires read on day two. It wasn't assigned to her. She just got tired of explaining the same six things.

People always ask about the numbers, so here they are. We merged 1,412 PRs, median review turnaround came down from 19 hours to 5, and the test suite went from 22 minutes to 7 after Dev's parallelization work in August. Next year we're going after the deploy pipeline. It's the last place where a bad afternoon can still eat a whole day, and we've been routing around it instead of fixing it for two years now.

Thanks for the reviews, the rollbacks, and the arguments in #eng-decisions. Especially the arguments.

The names, metrics, and migration details above are placeholders, so swap in your team's real ones before this goes out. Send me a few past posts and I can retune the voice drier, warmer, or blunter.
