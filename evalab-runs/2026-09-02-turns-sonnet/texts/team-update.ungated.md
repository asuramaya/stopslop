Team Update — August 2026

Migration's done. Everything's on the new cluster, no data lost, about two hours of downtime during cutover. Dashboard queries are ~30% faster too, which we'll happily take.

Priya (platform) and Marcus (frontend) joined this month. Both are ramping up — pairing sessions are open if you want to sit in.

Mobile slipped again, mid-September to early October. QA found two auth bugs in the post-migration build, and we're not shipping with known auth issues. That's twice now, so we're tightening the QA cycle to make the next date stick.

Thanks to Dana and Wei for covering on-call through the cutover.

CI's faster after last week's caching work. Still chasing a flaky payments test — ping me if you've seen it.

Appreciate the patience through two slips. Come find me if you've got questions about the timeline.
