# Dark mode is here

We shipped it. Took nine months longer than it should have, and I want to explain why, because "add dark mode" sounds like flipping a variable and it wasn't.

The problem was never the background color. It was your notes. People paste screenshots into notes. They paste tables from Excel with white cell backgrounds baked in. They highlight text in that specific yellow everyone uses. Invert the app naively and you get a black page with a blinding white rectangle sitting in the middle of it, which is worse than no dark mode at all.

So we did the boring thing. Every pasted image now gets checked for a dominant light background and dimmed by a factor you can override per-note. Highlight colors map to darker equivalents that hold roughly the same contrast ratio against the new background instead of screaming at you.

Three shades, not one. Dim for evening, Dark for most of the time, and something we internally call Cave, which is near-black OLED territory. Sarah on our design team runs Cave permanently and claims it saves her battery. I have not verified this claim.

Toggle lives in Settings, or press Cmd+Shift+D. It follows your system setting by default. You can pin it to always-dark if your OS switches at sunset and you hate that.

Known issue: PDF previews still render light. We know. It's on the list for the next release, along with the table borders that look slightly too heavy at Cave brightness.

Tell us what breaks.
