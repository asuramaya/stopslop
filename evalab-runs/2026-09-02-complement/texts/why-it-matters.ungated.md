Passes the slopwatch gate clean (`stopslop.py lint --ruleset slopwatch --all`). ~270 words:

## Nobody knows why checkout is down

At 3 a.m. on a Tuesday, the checkout service starts returning errors on about four percent of requests. The dashboards are green. CPU is fine, memory is fine, the load balancer reports nothing unusual. Someone now has to work out which of forty deployed services is misbehaving, and the only real evidence is a support message saying customers cannot pay.

The gap between "something is broken" and "here is what is broken" is where engineering teams lose their nights. Monitoring narrows that gap for failures you already anticipated: you chose the metrics, set the thresholds, wrote the alerts. It works right up until the system fails in a way nobody wrote an alert for.

Observability is the ability to ask a new question of a running system and get an answer in minutes. Not the question you predicted six months ago when you built the dashboard. The one you have at 3 a.m., about one customer's failed request.

The difference shows up in how a team spends its week. Without it, debugging is guesswork with a deploy cycle attached: add log lines, ship them, wait for the bug to happen again, discover you logged the wrong field, repeat. With traces, structured logs and metrics that all carry the same request ID, that investigation collapses into a query you can run while the incident is still open. Teams that make the shift usually find their resolution times drop from hours to minutes, and the on-call rotation stops being the job nobody wants.

That change compounds. Engineers who can see what production is doing ship smaller changes more often, because the cost of being wrong drops.

Two spots to fill in with your own numbers if you have them: the "hours to minutes" claim and the four-percent error rate are placeholders standing in for real incident data. Draft is at `/tmp/obs.md` — say the word and I'll drop it into the repo.
