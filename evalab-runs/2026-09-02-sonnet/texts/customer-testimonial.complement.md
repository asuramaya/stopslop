Our alerts used to fire an hour after the outage started, once someone noticed the dashboard was blank. Now the query that used to take four minutes across scattered instances runs in under ten seconds against one index, and the on-call engineer gets paged before customers do.

The migration itself took an afternoon. We pointed our existing shippers at the new endpoint, kept the old cluster running for a week as a fallback, and never needed it. Retention went from three days to six months, and nobody has to choose between "keep everything" and "keep the bill reasonable."

The part that changed how we debug is correlation. A trace ID from the API gateway now lines up with the worker logs, the database slow-query log, and the deploy marker from that morning, all in one search. Last month a customer reported checkout failures that only happened on mobile Safari; we found the failing request, the exact commit that introduced it, and the rollback target in under ten minutes, without paging three teams to compare timestamps by hand.

Support tickets that used to take a day of log spelunking now take fifteen minutes. That's the number our team actually tracks.

— Priya Raman, Staff Engineer, checkout platform
