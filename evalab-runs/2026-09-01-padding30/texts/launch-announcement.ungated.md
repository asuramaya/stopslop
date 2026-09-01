**Dark mode is here. Sorry it took a year.**

We shipped dark mode in Marginalia today. Settings → Appearance, or just let it follow your system.

The first version was the obvious one — invert the palette, dim the whites, ship it — and we killed it after two weeks of beta. About half the testers said their notes looked *wrong*. Not broken. Wrong. Highlighter yellow went radioactive against a dark page. Code blocks glowed. Anybody who pastes screenshots into their notes got a white rectangle punched through the middle of every entry.

So we rebuilt it around the assumption that your notes already have color in them, and that color has to survive the switch. The six highlighter shades each have a dark-mode twin, tuned by hand rather than by formula. Pasted images get a subtle border instead of floating in the void. Text sits at #E4E4E7 on #18181B, which measured out at 13.2:1 contrast — comfortably past WCAG AAA, and dimmer than pure white on black, which is what gives you that smeary halo effect at midnight.

Scheduling is per-device. My laptop flips at sunset; my phone stays dark all day because I mostly use it in bed. The theme also respects `prefers-reduced-transparency` if you have it on, which nobody asked for but two people will notice.

One known rough edge: PDFs still render light. That's a viewer-level fix and it's next on the list.

Update from the App Store or Play Store, or refresh the web app. Tell us what looks off — the highlighter tuning especially. We'll keep adjusting it.
