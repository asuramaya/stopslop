## Dark mode is here

We shipped dark mode in Margin 2.4. Turn it on under Settings → Appearance, or let it follow your system setting.

This took longer than it should have. The first version was a straight color inversion, and it looked awful. Pure white text on pure black burns at 1 a.m., which is when most of you write. So we backed off. Body text now sits at #D4D4D4 on a #16161A background, about a 12:1 contrast ratio, which is enough to read for an hour without your eyes complaining.

The harder part was inline content. Notes are full of code blocks, highlighter marks, pasted screenshots with white backgrounds, and links you colored yourself three years ago. We rebuilt the syntax theme from scratch instead of dimming the light one. Highlights lost about 40% of their saturation, because a yellow highlight in dark mode should still read as yellow and not as a flashlight. Pasted images now get an optional soft dim you can toggle per image.

We skipped an AMOLED true-black variant, per-notebook themes, and a scheduled switch at sunset, all on purpose. They are on the list. We wanted the default right first.

If you use a custom accent color, check it. A few of the lighter presets lose contrast against the dark canvas, and we would rather hear about it than guess. Reply here, or file it from the in-app feedback box.

Update from the App Store or your package manager. Windows and Linux builds ship Thursday.

---

Swap a few things before publishing. I invented the app name (Margin 2.4), the hex values, and the Thursday ship date as placeholders. Say the word and I'll drop in your real numbers, or retune the voice — this one is deliberately blunt and engineer-ish rather than upbeat.
