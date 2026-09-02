**Northwind Logistics: from fortnightly releases to 30 deploys a week**

Northwind Logistics builds freight-routing software for about 400 regional carriers. Through 2023 the team released every second Thursday. Release night started at 6pm and often ran past midnight, with four engineers on a call watching database migrations. Roughly one release in five got rolled back.

The delay lived in staging. A single shared environment served eleven teams, and a branch could wait nine days for a slot. By the time a change reached production it had been merged for two weeks, so when something broke nobody could say which of the 60 bundled commits did it.

Northwind adopted Riverbed CD in February 2024, starting with the pricing service. Riverbed spins up a disposable environment per pull request, runs the contract tests against it, and tears it down on merge. Deploys go out behind flags, one commit at a time, with automatic rollback when error rates cross a threshold for 90 seconds.

The pricing team went from 2 releases a month to 31 a week within a quarter. Six other teams followed by August. Across the company, lead time from merge to production dropped from 13 days to 40 minutes, and change failure rate fell from 19 percent to 4 percent. Release night no longer exists; the last scheduled after-hours deploy was in May.

"We used to plan our sprint around the release calendar," says Priya Raman, Northwind's VP of Engineering. "Now a fix for a carrier goes out the same afternoon they report it."

Northwind is moving its remaining four teams onto Riverbed by January 2025.
