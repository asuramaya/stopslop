# Security is not the security team's job alone

Last quarter we shipped 340 changes. The security team reviewed 41 of them. That gap is the whole problem, and no amount of hiring closes it.

Here is what we're changing.

Every team gets a security champion. Not a new title, not extra headcount. One engineer per team who spends roughly four hours a month on it: reviewing their own team's designs before they reach us, triaging the Dependabot noise, and being the person who knows how our secrets management actually works. We'll train them, and we'll pay for the training on work time.

Threat modeling moves into design review. If your design doc touches user data, auth, or an external boundary, add a section on what an attacker gets if they compromise it. Two paragraphs is fine. The point is that you think about it while the design is cheap to change, not after we've built it.

We're publishing our findings internally. Every pentest report, every incident writeup, redacted where it has to be. You cannot avoid a mistake you've never seen someone make.

We are not adding gates that block your merge. If security review becomes the thing standing between you and shipping, you'll route around it, and you'll be right to.

Ask questions in #security. There are no dumb ones, and the ones that feel dumb are usually the ones we've failed to document. If you find something broken, say so. Nobody gets in trouble for reporting a problem they created.
