# Dark mode is here

We shipped dark mode today. Open Settings → Appearance and pick Dark, Light, or Match System.

The obvious version of this feature would have been a color inversion. We tried that first and it looked terrible. White text on pure black causes halation, where letterforms smear at the edges, especially for people with astigmatism. So the background is a soft charcoal (#1B1B1F) and the body text sits at about 87% white. Contrast stays above WCAG AA at every text size we ship.

Two things took longer than expected. Highlights were the first: our yellow highlighter was tuned for a white page and turned into a glowing bar on a dark one. Every highlight color now has a dark variant with the saturation pulled down. The second was images pasted into notes. We don't touch them. A screenshot with a white background stays a screenshot with a white background, because dimming user content is a good way to make people think their file got corrupted.

Match System follows your OS setting and switches at sunset if that's how your machine is configured. The transition is instant with no fade, which was a deliberate choice after several people told us the animated version felt sluggish when they were switching between apps.

Code blocks get their own palette. If you write a lot of technical notes, the syntax colors were rebalanced for the dark background rather than reused from light mode.

Available now on iOS, Android, macOS, and the web app. Windows lands next week.
