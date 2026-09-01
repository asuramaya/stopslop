**Security isn't the security team's job**

We have four people on the security team. We have about 180 engineers. Do the math on who is actually writing the code that gets attacked.

That ratio isn't a staffing complaint. It's the whole argument. Four people cannot review every pull request, and they were never going to. What they can do is build the guardrails, answer the hard questions, and handle the incidents. Everything else lands on us.

Here's what "everyone's responsibility" means in practice, and it's smaller than it sounds.

Notice the risky thing and say so. If a PR adds a new external call, touches auth, or moves customer data somewhere new, flag it in review. You don't need to know the fix. Naming the concern is 90% of the value.

Ask early, not at the end. A design doc question costs an hour. The same question the week before launch costs a sprint. #sec-help is not a queue for emergencies — use it while you're still sketching.

Report your own mistakes. Nobody gets in trouble for a leaked key they reported. The bad outcome is the one we find in a log six months later.

Do the training. Yes, it's tedious. It takes 40 minutes and it's how we stop repeating last year's incidents.

None of this makes you a security engineer. It makes you someone who doesn't quietly hand the security team a problem they can't see.

Questions, disagreements, "this rule is dumb because X" — bring them to #sec-help. Especially the last one.

---

Swap the headcounts, channel name, and training length for your real ones — those are placeholders.
