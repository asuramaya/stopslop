# What We Took Home From ScaleConf

Six of us went to ScaleConf last week. We came back with three pages of notes and one argument we still haven't settled.

The talk that landed hardest was Priya Raghavan's on incident review. Her team stopped writing postmortems for outages under fifteen minutes. Their reasoning: the writeups were consuming four engineer-hours each and nobody read them. Instead they tag the short incidents and review the tags monthly, looking for clusters. Marco pointed out on the flight back that we have roughly forty of those a quarter and we write all of them up. We're going to try Priya's version through October and see what we miss.

Two of us skipped the keynote for the hallway track, which turned out to be the better call. Dana spent an hour with an engineer from Lumen who had migrated off the same queue library we're stuck on. She sent us her notes that night. They took eleven weeks, not the four we'd budgeted, and the pain came from consumers nobody had documented.

The vendor floor was mostly noise. One exception: a small team demoing schema diffs against production traffic. We booked a call for the 14th.

The argument we haven't settled is whether any of this applies at our size. Priya's team runs 200 engineers. We run nine. Half of us think the tagging system collapses without volume; the other half thinks we should try it anyway and find out. We'll decide at Thursday's planning session.
