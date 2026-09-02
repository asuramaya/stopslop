**Dark mode, finally**

We shipped dark mode today, in version 3.2, on iOS, Android, web, and desktop.

It took us longer than it should have, and the holdup wasn't the palette. It was everything you paste into a note. Screenshots with white backgrounds, code blocks from three different editors, tables pulled out of a spreadsheet, a PDF page someone dropped in at 2 a.m. Flip the shell to dark and half of that turns into a lightbulb. So we rebuilt how notes render embedded content: images get a thin border instead of a glowing rectangle, code blocks carry their own theme, and pasted HTML has its hardcoded background colors stripped before it reaches the page.

Body text sits at #E4E4E7 on #18181B. Grey on near-black, not white on black — at 21:1 contrast the letters bleed at the edges, and anyone reading for an hour straight will feel it even if they can't name it.

You can switch three ways. Pick it in Settings → Appearance, follow your system theme, or schedule it to flip at sunset. New installs follow the system by default.

Two things are unfinished. Exported PDFs still print light, which was our call — tell us if it's the wrong one. And iPad ink still lays down black strokes on the dark canvas; the light-ink pass lands in 3.3.

If a note of yours looks broken in the dark, send us a screenshot. The weird ones are the ones we want.

Swap in your app name and support address — I left those out rather than invent them.
