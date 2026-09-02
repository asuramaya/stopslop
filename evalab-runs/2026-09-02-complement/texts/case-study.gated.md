## Ferrymark Logistics went from six releases a year to eleven a day

Ferrymark shipped its dispatch platform on a calendar. Four planned releases, two emergencies, and somebody's Saturday burned on each one. The runbook ran to 140 manual steps, and only two engineers knew it well enough to drive. When either took a holiday, the window moved. The migration itself took eleven weeks, and most of that wasn't platform work at all. It went into writing the tests that the billing service had never had.

Deploys stopped being events on anyone's calendar.

What changed first was that runbook. One hundred forty steps became nine automated gates and a single human approval, which is now a director clicking a button in Slack while waiting for coffee.

Twelve months in, Ferrymark pushes eleven deploys a day where it used to manage six a year. Merge to production fell from four days to 22 minutes. The change failure rate dropped from 31 percent to 4.2, and mean time to restore came down from six hours to eighteen minutes. That last pair is what caught them off guard. They had braced for more breakage in exchange for speed and got the opposite, because a 40-line change that breaks something tells you exactly where to look, while a quarterly release does not.

"We stopped negotiating about what makes the cut," says Priya Raghunathan, VP of Engineering. "That argument used to eat a full week every quarter."

Ferrymark now runs the same pipeline for its warehouse scheduling product. The billing tests, written under protest in week three, have caught 47 regressions.
