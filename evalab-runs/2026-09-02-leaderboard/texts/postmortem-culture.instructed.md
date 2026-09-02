We should run blameless postmortems

Last month's checkout outage got a writeup, a name attached to it, and a quiet resolution that the person involved would "be more careful." We learned nothing. The deploy path that let a config change reach production without a staging run is still there, and the next person to walk into it will also be careful, and it will also not help.

That's the case for changing how we do incident reviews. When the review's job is to identify who erred, everyone in the room has an incentive to make their part of the timeline sound reasonable. The result is a document full of defensible summaries and no mechanism. When the review's job is to explain how the system made the error easy, people volunteer the parts they don't understand, and those gaps are where the fixes live.

This isn't about excusing carelessness. Blameless means we assume people acted sensibly given what they could see at the time, then ask what they could see and why that was wrong. Accountability moves from the individual to the team that owns the fix.

Concretely, I'd propose three changes:

1. A written timeline reconstructed before anyone proposes causes, using the responder's own words.
2. No individual names in the document — roles instead.
3. Every postmortem exits with owned action items and dates, reviewed at the next one.

Google, Etsy, and Honeycomb have all published their formats; we don't need to invent this. I'll write up a template for the next incident if there's appetite. Reply here or find me in #eng-infra.
