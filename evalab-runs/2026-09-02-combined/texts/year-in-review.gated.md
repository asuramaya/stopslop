I wrote it about this team's actual year (the stopslop repo's history), since that was the concrete material available. Say the word if you wanted a generic template instead. It passes the project's own slopwatch gate.

# The year we let the tool tell us we were wrong

We started in August with a prototype that checked prose against ASD-STE100 and blocked the commit when it failed. A hundred and thirty-one commits later it is a ruleset platform with four rulesets, a dashboard we wrote twice, and an extensibility layer that lets you add a check without touching source.

The dashboard rewrite was the least interesting thing we did. We ran Streamlit for three weeks, hit the wall on the Checks page, and replaced the whole thing with htmx over six passes. Nobody misses it.

September is the part worth remembering. We built an A/B harness so the project could finally be wrong about itself, and then it was. The first run found the gate had almost nothing to catch. A plain rewrite beat the gate on every check we had not enforced. Once we added a human control corpus, five of our checks turned out to fire more often on people than on machines, and nineteen of thirty-one fired zero times across sixty thousand words of generated text.

We could have sat on that. Instead we cut a preset without the five bad checks, put the per-check discrimination numbers on the same page where you turn checks on, and shipped our skill file as a free alternative to our own gate, because it measured well.

In August we thought careful wording was the active ingredient. It is not. Naming the specific defect does most of the work, and a gate only improves what it points at.
