I don't know which conference or team, so I've written it as a concrete engineering-team recap with one bracketed name to swap. Everything else is specific enough to edit rather than fill in.

---

**What we brought back from [Conference]**

Four of us went. Three days, something like forty talks between us, and the honest tally is that two of them changed what we're doing on Monday.

The first was a postmortem talk — a payments team walking through an outage they caused with a config change that passed every test they had. Nobody clapped at the end. People just sat there. We came home and audited our own config path and found the same gap: staging reads a different secrets store than prod, so a whole class of mistake can't fail until it fails on customers. That's now a ticket.

The second was smaller. A two-person shop demoed their internal search over incident notes, and the interesting part wasn't the model, it was that they'd spent six months just getting engineers to write the notes. The tooling was the easy half.

The hallway track was better than the main stage, which is the usual verdict and still true. Three separate people told us unprompted that they'd ripped out a vendor we're currently evaluating. Worth knowing before the contract, not after.

The thing we didn't buy: every other booth had the same pitch, more or less word for word, and none of them would name a customer running it at our scale. We asked five times.

Slides and our raw notes are in the shared drive. Ask us anything — we're still arguing about the second talk.
