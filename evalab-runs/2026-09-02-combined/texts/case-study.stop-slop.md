Meridian Freight sells routing software to 400 trucking companies. Two years ago the team shipped once a month. Priya Raghavan, who ran release engineering, kept Fridays clear because she spent them fixing what her team broke on Thursday night.

Each release cost eleven hours. Four engineers worked down a spreadsheet of manual steps, and when step 30 failed, someone restarted at step one. Twice in 2023 they rolled back and pushed a month of work into the next cycle.

They moved to Lattice CD in March 2024. Priya converted the spreadsheet into pipeline definitions and put every service behind a feature flag. Marcus Oyelaran rewrote the database migration so it ran ahead of the deploy rather than in the middle of it. The first automated release went out on a Tuesday afternoon and finished in nineteen minutes.

Meridian ships 40 times a week now. Engineers merge to main and see their change reach customers before lunch. Priya deleted the release calendar.

Her team watches three numbers. Change failure rate dropped from 22 percent to 4. Median time from merge to production fell from 31 days to 40 minutes. Support tickets about routing errors halved, because an engineer fixes the bug the day a dispatcher reports it.

"I used to schedule my life around Thursdays," Priya says. "Now I have to look up when we deployed if someone asks."

Marcus counts a different win. Two engineers who joined in January shipped code to customers during their first week. He spends his review time on the code itself.
