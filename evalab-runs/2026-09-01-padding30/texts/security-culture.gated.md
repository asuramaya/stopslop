**Security isn't the security team's job**

We have four people on the security team. We have about 190 engineers. Do the math and you'll see why the current setup doesn't work: four people cannot review every PR, every Terraform change, every new dependency, every S3 bucket someone spins up on a Friday afternoon.

Last quarter, three of our five worst findings came from code that had been through review. Not sloppy review — normal review, by good engineers who were looking at correctness and readability and weren't thinking about whether that endpoint checked authorization. Nobody was negligent. The question just wasn't in anyone's head.

So here's what I'm asking for, and it's small.

When you review a PR, ask one question you weren't asking before: *what happens if the person calling this is hostile?* That's it. Not a threat model. One question. If the answer takes more than a minute to work out, tag `#sec-help` and we'll look at it with you — no ticket, no process, no judgment about not knowing.

Two things we're changing on our side. Office hours move to Tuesdays 2–4pm, drop-in, no agenda required. And we're killing the security review queue for low-risk changes, because a two-week wait taught everyone to route around us, which is worse than no review at all.

I'd rather you ping us about ten things that turn out to be fine than stay quiet about the one that isn't. Asking is cheap. We have the capacity for it. Use it.

— Dana, Security
