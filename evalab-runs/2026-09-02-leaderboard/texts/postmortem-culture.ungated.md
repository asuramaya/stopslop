Clean through the slopwatch gate. ~260 words:

---

**Proposal: run our incident reviews blameless**

Every review I've sat in ends the same way. Someone explains what they did, everyone nods, and the write-up quietly settles on a name. The action items are real, but they're small: add a check, add a warning, remind people to be careful. Six weeks later the same class of failure comes back wearing different clothes.

That's not because we hire careless people. It's because a review that is looking for a person stops looking once it finds one. The interesting part of an incident is everything upstream of the last click: the deploy tool that made the dangerous option the default, the runbook that went three months stale, the alert that fired at 2am into a channel nobody watches. None of that surfaces if the engineer closest to the failure is busy managing their own exposure.

Blameless doesn't mean consequence-free, and it isn't a kindness policy. It's a data-collection technique. You get an honest timeline, including "I didn't know what that flag did" and "I skipped the staging run because it takes 40 minutes," only when saying those things is safe. Honest timelines are where the systemic fixes live.

Concretely, I want to try three things: reviews written in terms of systems and signals rather than people, a facilitator who sits outside the reporting chain, and no individual named as a cause in the document. Names stay in the timeline as actors, not as answers.

Let's run the next three incidents that way and compare the action items against the last three. If the fixes aren't bigger, we drop it.

---

The examples in paragraph two are generic on purpose — swapping in two real incidents everyone remembers will do more work than anything else here.
