Security stopped being the security team's job here about eighteen months ago, and most of you noticed when the on-call rotation changed.

The reason is arithmetic. We have six people on AppSec and roughly four hundred engineers shipping code. Six people cannot read four hundred people's pull requests. When we tried, review queues ran nine days deep and teams routed around us by shipping behind feature flags and asking forgiveness later. So we changed who does the work.

Here is what that means on a Tuesday. You own the threat model for your service. Not a document AppSec writes about your service, but a page you keep current, in your repo, that says what an attacker wants from you and what stops them. You handle the dependency alerts for your own package files. You write the abuse case into the test suite alongside the happy path.

AppSec still exists and their job changed. They build the paved road: the auth library you should use instead of rolling your own, the secrets scanner in CI, the office hours every Wednesday where you bring a design and Priya tells you where it leaks. They review the hard things, crypto, payment flows, anything touching customer PII at scale.

Some of you will find this annoying. Fair. It adds work to sprints that already run tight, and I would rather say that plainly than pretend the tradeoff away.

Ask your manager for the threat model template. If your service has no owner listed in the registry by the end of the month, AppSec will assign one, and you will not enjoy their choice.
