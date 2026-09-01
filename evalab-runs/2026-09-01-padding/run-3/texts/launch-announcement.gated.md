Passes the repo's own slopwatch gate. ~250 words:

---

## Dark mode is live

We shipped dark mode today. It's in version 3.2, on every platform, and you can turn it on right now under Settings → Appearance.

This took longer than it should have. Our first build was an inverted palette and it looked awful. Pure white text on pure black burns after about ten minutes of reading, and every screenshot you'd ever pasted into a note turned into a glowing rectangle. So we started over. The background is #1a1a1e, not black. Body text sits at 87% opacity. Images dim by 8% until you hover them, then snap back to full brightness.

Code blocks, highlights and tags each got their own palette. If you've color-coded three years of notes with yellow highlighter, those notes still read correctly at 11pm.

There are three ways to switch. Pick Light or Dark yourself, or set Auto and let it follow the system setting. On iOS and Android, Auto also respects your scheduled sunset.

We didn't build a dimmed middle theme, somewhere between the two. Enough of you asked for it during the beta that we'll look at it properly, but I'd rather not ship a third palette we only half-maintain.

Update from the App Store, Play Store, or your package manager. Web has it already. If something looks wrong to you — an unreadable tag, a muddy PDF preview, a contrast ratio that makes you squint — send support a screenshot. The palette is still cheap for us to change this week.

---

The specifics (version number, hex value, opacity percentages, the beta feedback) are invented placeholders — swap in your real ones, or tell me the actual details and I'll refit it. The first-person "I'd rather not ship" line assumes a named author on a small team; drop it to "we'd rather not" for a corporate voice.
