We shipped the billing rewrite in March, six weeks after the date we gave in January. Priya traced the delay to the old ledger, which wrote two rows for each refund. Nine downstream jobs carried patches for that quirk. She removed 3,800 lines of patch code once the new ledger landed. Marcus rebuilt the test harness in April, so a full run finishes in four minutes instead of thirty-one. That one change did more for our release pace than the three quarters of process work before it.

Deploys went from twice a week to eleven times a day.

We broke production twice. The June outage lasted 47 minutes and started when I approved a schema migration without checking read replica lag. Dana wrote the postmortem. We now block migrations when a replica falls more than 30 seconds behind. The October incident ran 9 minutes, and Sam caught it from the alert we added in June. Four engineers joined and one left. Wei has carried the pager since August and closed 60 percent of the tickets that came in over that stretch.

We promised to retire the Python 2 service and to move search off the primary database, and we did neither. Both slipped because the billing rewrite ate the second quarter. They go at the top of the January plan, ahead of anything new.

Next year I want us to cut the median wait for PR review. It sat at 19 hours this year, and most of that time a reviewer had the tab open and never got back to it. Bring your ideas to the offsite.
