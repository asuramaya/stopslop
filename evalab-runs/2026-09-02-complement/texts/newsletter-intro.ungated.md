Every codebase has a room nobody opens. Ours has a few. This month we're opening them.

The phrase "technical debt" gets stretched to cover anything we dislike about the code, which makes it useless as a planning tool. Ward Cunningham's original version was narrower and more honest: you ship something you know is wrong because shipping now is worth more than shipping right, and you pay interest until you fix it. That's a trade, made on purpose, with a payment plan. Most of what we call debt is not that. It's mess — code nobody chose, written under deadline by people who have since left, load-bearing in ways the tests don't cover.

Both are worth writing about, and they need different treatment. Deliberate debt needs a ledger. Mess needs an archaeologist.

In this issue: Priya walks through the retry logic in the billing service, and how three years of one-line fixes turned into a state machine nobody ever drew. Marcus argues that our test suite has become a liability. And we have numbers from the July migration, including the parts that went badly.

Read the archaeology piece first. It's the one that will change how you review.

---

~200 words. Contributor names, the billing service, and the July migration are placeholders — swap in your actual pieces.
