I'm nominating the Release Engineering team for the [award name].

When they took over deploys last January, a production release took 47 minutes and ran through nine manual steps. Two people had to be online for every one, so we shipped on Tuesdays and Thursdays and shipped nothing at all in December.

They rebuilt it in stages. The checklist became a script. The script became a pipeline with automatic rollback on failed health checks. Then they added canary stages, so a bad build reaches 5% of traffic instead of everyone. They wrote a new runbook and later deleted most of it, because the steps it described no longer exist.

A deploy now takes 6 minutes and starts on merge. We went from 8 releases a month to 340. Rollbacks fell from one in every 5 releases to one in 40, and the last three ran on their own at 2am with nobody watching.

They did all of this with no code freeze, no rewrite, and no new process for anyone else to learn. Ask around the engineering org and most people can't tell you when the migration happened, because on their side nothing broke.
