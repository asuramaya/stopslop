# FY26 in review

We shipped the billing rewrite in March, four months later than planned. The delay came from a schema decision we made in January and reversed in February. The postmortem is in the wiki; the short version is that we let one team own a table five teams wrote to.

Deploys went from twice a week to about eleven a day after Priya finished the pipeline work in June. Median time from merge to production is now 9 minutes, down from 3 hours. Rollbacks went up too, from 2 a month to 14, which is the trade we wanted.

We hired six people and lost two. Time from a new hire's first day to their first production commit is down to 4 days from 3 weeks, mostly because Dev spent two weeks in April making the local environment work on a fresh laptop without anyone's help in Slack.

The on-call rotation is still bad. Pages are down 40% year over year, but the 2am ones are not, and they cluster in the payments consumer. We know why. We have not fixed it. It is the first thing on next quarter's list.

Things we killed: the internal feature flag service, the staging cluster nobody trusted, and the Thursday architecture meeting.

Things we tried that did not work: the monorepo migration, which we stopped at 30% and reverted, and the ML alert triage, which flagged everything.

Thank you for a hard year. FY27 planning starts September 15.
