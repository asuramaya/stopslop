Vantage Freight sells logistics software to 600 trucking firms. In March 2024 the team released once a quarter. Each release took nine engineers and a Saturday. Rollbacks happened twice a year, and each one cost the support desk a full week of calls.

Priya Raghavan, who runs platform engineering, moved the release process onto Corridor in June 2024. The migration took eleven weeks. Her team rewrote 340 Jenkins jobs into Corridor pipelines and pulled integration tests off the shared staging box, so each service got its own deploy path.

By January 2025 Vantage deployed 40 times a week. Median lead time from merge to production dropped from 23 days to 4 hours. The change failure rate settled at 3 percent, down from 11.

"We stopped scheduling releases," Raghavan said. "Engineers merge, and the code reaches customers before lunch."

The support desk noticed before anyone else. Ticket volume in the week after a release fell 62 percent, because Vantage no longer bundles 90 changes into one night. One engineer reverts one commit when something breaks now.

Two decisions carried the migration. Raghavan kept the old Jenkins pipeline running for six weeks next to Corridor, so no team faced a hard cutover on a date it did not pick. She also paid down the test suite first: 1,400 flaky tests went into quarantine before a single pipeline moved.

Vantage runs Corridor across 62 services and 140 engineers today. Raghavan wants preview environments on each pull request next, which she expects will cut a day off review time for the mobile team.
