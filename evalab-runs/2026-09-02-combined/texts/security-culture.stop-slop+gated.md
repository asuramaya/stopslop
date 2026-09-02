You own the security of the code you ship

Four people sit on our security team. Last quarter they read 1,900 pull requests, caught a hardcoded Stripe key in billing, and found an analytics bucket open to the internet. They also missed the session fixation bug a customer reported in June. Four reviewers cannot cover what six squads write.

Starting October 1, each squad names a security owner. The role rotates every quarter, so the knowledge spreads past one desk. That owner writes the threat model section in your design docs, triages Dependabot alerts for your services, and signs off before a release touches customer data. Priya's team stops reviewing routine pull requests in exchange. They are building secret scanning into pre-commit and a paved auth path you can adopt in an afternoon, and they keep the hard reviews, the pen test vendor, and incident response.

Never written a threat model? Office hours run Thursdays at 2pm. Bring a design doc and you will leave with a filled-in template and a list of fixes.

I want two things from you this month. Read the secure coding guide in the handbook, which runs ten pages. Then pick one service you own and trace where untrusted input enters it. Most of our incidents last year started at a boundary someone assumed was internal, and the trace takes an hour if you have the service map open.

You don't need to become an appsec engineer. Notice when something looks wrong and say so before it ships. The engineer who flagged that open bucket had been here five weeks and had no security background. She asked why the URL worked from her phone.
