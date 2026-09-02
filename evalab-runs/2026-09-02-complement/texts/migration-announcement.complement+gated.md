Subject line — Northwind Analytics moves to Cascade in Q1

Starting January 12, Northwind Analytics will run on Cascade, the platform we've spent the past year building. Your account, saved reports, dashboards, and API keys move with you, so you don't need to rebuild anything.

Migration happens in waves by account size, smallest first. You'll get an email fourteen days before your wave, with your exact cutover window. Each account is offline for roughly two hours during the move, and we've scheduled every window between 01:00 and 05:00 in your account's primary timezone.

Three things change on day one. Report exports arrive as Parquet by default instead of CSV; CSV stays available as an option in export settings. The v2 REST API replaces v1, which we'll keep running read-only until June 30. And scheduled reports move to a new scheduler that supports sub-hourly intervals, which customers have asked for since 2023. Two things we know will annoy people: custom SQL blocks written against the old warehouse schema need updating, and browser-saved bookmarks to specific dashboards will break because dashboard URLs change format. For the SQL, we've published a mapping table and a script that flags queries needing changes. For the bookmarks, we'll serve redirects for ninety days.

Your billing stays exactly as it is now. Same plan, same price, same renewal date.

If you want to move early, you can opt into the December pilot wave by replying to this email. If you want to move late, tell us and we'll push you to the final wave in March. Questions go to migration@northwind.example or your account manager, and we'll publish a status page at status.northwind.example on December 1.
