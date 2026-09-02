Security isn't a team you hand things to

Four people on AppSec. A hundred and eighty engineers shipping. That ratio is why the review queue backs up every quarter.

Hiring doesn't close it. Doubling the team still leaves us at one reviewer per 22 engineers. So we're moving the work to where it already sits. Starting next sprint, whoever writes the code owns its threat model. Not a document. The PR description gets three questions. What's the untrusted input here? What happens if it's hostile? What's the blast radius if this service is fully owned? If you can't answer the third one, that's the finding.

AppSec stops being a gate and becomes a help desk.

They'll pair with you for an hour on anything you flag, and they'll keep owning the parts that genuinely need specialists: crypto, auth, anything crossing the payments boundary. They will stop rubber-stamping your dependency bumps. Two numbers tell us whether this works.

Time-to-merge on security-touched PRs, and the share of findings caught before review rather than after. Last quarter that second one was 11%; I want 50% by December. Worth saying out loud that "everyone's responsibility" is the standard way a thing becomes nobody's. That's why every service has a named owner in the catalog, and why those three questions live in the PR template where skipping them is visible. Culture without a mechanism is a poster.

Ask in #appsec-help. Nobody gets judged for asking early. The expensive questions are the ones asked after launch.

Numbers, channel name, and dates are placeholders — swap in yours and the post holds.
