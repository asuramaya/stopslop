**Who owns security here**

We have four people on the security team and about two hundred engineers. Do the arithmetic and you get our current situation: a queue, a review that lands three days after you needed it, and a habit of treating security sign-off as a customs checkpoint to smuggle things past.

That worked when we shipped monthly. We ship forty times a day now.

So here's the shift. The security team stops being the approver and becomes the toolmaker. They own the paved road: libraries that handle auth correctly, the secret scanner in CI, service templates with sane defaults already set. You own what you build on top of it.

Three things change for you.

If your feature touches customer data, you write the threat model. One page. Who wants this data, how would they get it, what stops them. Not a form to fill in — a paragraph you actually thought about.

If something smells wrong in someone else's PR, say so in the PR instead of DMing security. The review is the place.

If you find a problem in our own systems, report it and nothing bad happens to you. That's a promise from me, in writing. Whoever reports the hardcoded key they committed last year is doing us a favor, not confessing to something.

Office hours start next week, Tuesdays and Thursdays. Bring the ugly stuff.

None of this makes security someone else's problem. It makes it yours, with better tools than you had last quarter, and with four people whose whole job is making that easier.

---

~255 words. The headcount, ship rate, and office-hours days are placeholders — swap in your real numbers, since the arithmetic in the opening is what makes the argument land.
