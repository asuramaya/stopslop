Security belongs to the person writing the code

Last quarter Priya and Marcus reviewed 312 pull requests between them. They flagged nine problems. One of those, an auth token we wrote to the application log in plaintext, sat in staging for six weeks before Marcus read the diff.

Four reviewers cannot keep pace with 140 engineers who ship twice a week. From Monday, you own the security of what you merge.

In practice:

Before you open a PR, write two lines in the description about who could abuse the change and what they would gain. If you cannot name an attacker or a payoff, you do not understand your own change yet.

Read a new dependency's network calls and install scripts before you pull it in. Ask Priya if the answer is unclear.

If you see a hardcoded credential in someone else's branch, say so in a comment. No security title required.

The AppSec team will stop working the review queue by volume. Priya and Marcus will spend that time on the auth service and the payment path, and they will hold office hours on Wednesday afternoons. Bring them a design before you build it, not a finished branch you cannot afford to throw away.

Some of us will miss things. I want to hear about those. Tell me about a leaked key on the Tuesday you find it, and I will back you. Read about it in a customer's email in March and we both have a harder problem.
