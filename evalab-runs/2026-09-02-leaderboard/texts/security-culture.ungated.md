**Security isn't a team down the hall**

We have four security engineers. We have roughly two hundred people shipping code. You can do that division yourself.

So when someone says security should be "everyone's responsibility," the honest version isn't a motivational poster. It's arithmetic. Four people cannot review every pull request, and they were never going to.

What I'm asking for is smaller and more specific than a culture change.

One: put a threat section in your design doc. Three sentences. Who would want to break this, what would they get, what stops them. If you can't answer the second one, say so — that's useful information, and it's the point where a security review costs an hour instead of a quarter.

Two: when you find something, file it. Not to the team lead, not in a DM to Priya. File it. Last year, 40% of the issues we found internally came in through side channels and sat for weeks because nobody owned them.

Three: stop treating a security finding on your code as a performance event. It isn't one, and we will not treat it as one. The engineer who reports their own mistake on Friday saves us the weekend.

Security's job changes under this model. They stop being a gate and start being the people who build the paved road — the linters, the libraries, the default configs that make the safe thing the easy thing. That only works if the rest of us actually walk on it.

Questions, my calendar's open.
