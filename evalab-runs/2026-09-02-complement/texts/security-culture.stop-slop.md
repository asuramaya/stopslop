Security belongs to whoever writes the code. We have four people on the security team and about ninety engineers shipping against them. That ratio settles the outcome before anyone files a ticket.

Priya's team read 340 pull requests last quarter and flagged 11 problems. Nine of the eleven were things the author could have caught: a token committed to a config file, an endpoint that skipped the auth middleware, a dependency sitting two majors behind a published CVE. Review found them when the branch was three weeks old and the author had moved on to other work. The fix then cost a day instead of ten minutes.

Two things change Monday.

Each team names a security owner. That person reads the dependency alerts for their services and files the upgrade PRs. Rotate the role quarterly if you want, but put a name in the team charter by Friday.

Second, run the threat-model template against any design doc that touches customer data or payments. Do it before the design review. Bring the filled template to the meeting the way you bring the migration plan.

Priya's team will spend the recovered hours on the pen test schedule and on auditing the vendor code we run but did not write. They will still answer questions. They will stop being the last gate before merge.

If you spot something and cannot tell whether it matters, post it in #sec-help with the file path. You will not get judged for a false alarm. Andrew raised three last month and one of them was a live session-fixation bug.
