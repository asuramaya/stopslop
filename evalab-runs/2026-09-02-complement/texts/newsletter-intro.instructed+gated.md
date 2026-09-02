Welcome to the September issue. This month we're talking about technical debt, which is a phrase most of us use to mean two different things and then argue past each other about.

There's the debt we took on deliberately. The auth shim we wrote in a weekend before the launch, knowing it wouldn't survive contact with SSO. That was a trade, we made it with open eyes, and the interest payments were priced in. The other kind is the code nobody chose, that accumulated because three teams each solved half a problem and the seams were never closed. Nobody signed for that one. It's harder to talk about because there's no decision to point back to.

Both cost us. In our last quarter, changes touching the billing service took a median of 11 days from first commit to production, against 3 days for everything else. That gap is the closest thing we have to a number on this.

This issue carries three pieces. Priya on why the payments rewrite stalled twice before it worked, a short piece from the platform team on deleting 40k lines of dead config, and notes from the deprecation review we ran in August. Most of it is unglamorous. That's the subject.
