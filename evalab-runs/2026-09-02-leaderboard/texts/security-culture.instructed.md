# Security is not just the security team's job

We have four people on the security team and about 180 engineers shipping code. That ratio tells you everything about why review-at-the-end doesn't work. By the time a design reaches security review, the decisions that matter — where data lives, who can read it, what the service trusts — were made weeks ago. We either wave it through or ask you to rebuild something that already works.

So we're changing where security happens.

Starting this quarter, every team names a security champion. Not a second job, and not a title. It's one person per team who gets a half-day of training, a direct line to the security team, and standing permission to say "let's think about this before we build it." Champions don't approve anything. They ask the questions early, when answering them is cheap.

Three things we're asking of everyone else. Write threat notes in design docs — two paragraphs on what an attacker gains if this component is compromised. File security bugs like any other bug, in the same tracker, with the same priority conversation. And when you're unsure whether something is a problem, ask in #security-questions instead of guessing. We have never once been annoyed by a question that turned out to be nothing.

What we're giving back: faster reviews for anything that arrives with a threat note, no more surprise blocks the week before launch, and a monthly writeup of what actually got reported so you can see where the real risk sits.

The security team stays accountable for the program. Everyone else owns the code they write, which is where the vulnerabilities live anyway.
