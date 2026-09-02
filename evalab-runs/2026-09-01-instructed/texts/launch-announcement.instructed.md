# Dark mode is here

Dark mode shipped today. Open Settings → Appearance and pick Dark, Light, or Match system.

We built it because of when people write. Looking at anonymized session start times from our own usage logs, 31% of note sessions begin after 9pm. A white page at that hour is unpleasant, and until now the only fix was your operating system's inversion filter, which mangled images and code blocks.

The theme is a real palette, not an inversion. Backgrounds sit at #16181C rather than pure black, because pure black next to white text produces halation on OLED screens and makes small type harder to track. Code blocks get their own syntax theme. Highlighter colors were remixed so that yellow highlight on a dark background still reads as a highlight and not a bruise.

Match system follows your OS setting and switches at whatever hour you've set for night shift. If you'd rather it not change under you mid-sentence, pin it to Dark or Light and it stays there across devices.

Two things we know are still rough. Embedded PDFs render on their original white page, so opening one in a dark note is a flash of brightness; we're working on a page-tint option. And custom note colors set before this release can land at low contrast against the dark background. There's a one-click "adjust for dark" button in the note menu, and we'd rather offer that than silently rewrite colors you chose.

Available now on iOS, Android, and web. Desktop lands next week.
