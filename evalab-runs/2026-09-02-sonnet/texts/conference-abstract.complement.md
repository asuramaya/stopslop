Breaking Apart the Monolith: What We Got Wrong Before We Got It Right

Three years ago our checkout service, inventory system, and notification logic lived in one 400,000-line Rails application. Every deploy touched every team. A bug in the shipping calculator could take down account login. This talk walks through the migration we ran to split that monolith into fourteen services, and the mistakes that cost us the most time.

We started by extracting the wrong boundaries: services organized around database tables instead of business capability, which left us with the same coupling in a new shape. We rebuilt the split around domain ownership, added a message queue for cross-service events, and spent four months on data consistency once transactions no longer covered the whole system.

I cover the concrete decisions: how we chose which service to extract first, how we handled the shared database during the transition, what broke in production, and how our on-call load changed before and after. I close with the numbers, including deploy frequency, incident count, and the operational cost of running fourteen services instead of one.

If you are considering this migration or midway through one, you will leave with a checklist of the decisions that mattered and the ones that did not.
