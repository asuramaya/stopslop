# Dark mode is here

Dark mode shipped today in version 3.2. Open Settings, then Appearance, and pick Dark. It applies immediately, no restart.

We built it because the request came in constantly — 1,400 mentions in support tickets and feature votes over the past year, more than any other single ask. Most of those came from people who write at night, in bed, or in a shared room where a bright screen is a nuisance to someone else.

The version we shipped is the fourth one we tried. The first three were the naive approach: invert the palette, darken the background, call it done. That produced notes that were technically dark and genuinely unpleasant to read. Pure black backgrounds with pure white text create halation, where letters seem to bleed at the edges, and it gets worse the longer you read. So the background is a dark gray (#16181D) and body text sits at 87% white. Contrast measures 13.4:1, above the WCAG AAA threshold of 7:1.

Code blocks, tables, and highlighted text each needed their own treatment. Yellow highlighter on a dark background is close to unreadable, so highlights render as a muted amber wash instead of a solid fill. Syntax colors were re-picked for the dark palette rather than reused.

There is also an Auto setting that follows your operating system's appearance, so notes switch when your phone does at sunset.

Exported PDFs stay light. Nobody wants to print a black page.

Update from the App Store, Google Play, or your desktop app's update menu. Web is already on it.
