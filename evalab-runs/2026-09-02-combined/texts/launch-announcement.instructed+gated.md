# Dark mode is here

Dark mode ships today in version 3.2, on iOS, Android, and the web app.

It was the most-requested feature in our feedback tracker for two years running, with 1,840 votes. We put it off longer than we should have, and the reason is unglamorous: our editor rendered note content through a theme layer that assumed a white page. Rewriting that layer took four months of work that users never see.

The result covers everything, not only the app chrome. Code blocks, tables, inline highlights, math rendering, and the PDF preview all have dark variants that were designed rather than inverted. Images in your notes stay untouched, since dimming them made photos look muddy in testing. You can set it three ways: follow the system setting, force it on, or switch on a schedule by time of day. Look under Settings, then Appearance. On iOS the app follows the OS with no restart.

Two things worth knowing about the colors.

Our background is #14161A rather than pure black, because pure black next to white text produces visible halation for many readers. OLED users who want true black can turn it on separately under Appearance, and it does save battery on those screens. We also raised the contrast of the default light theme while we were in there: body text went from #4A4A4A to #2B2B2B, which brings it to WCAG AA against the page background. Nobody asked for that one. The old value had been bothering us for a while, and the theme rewrite made it a two-line change.

Update from the App Store, Play Store, or reload the web app. The 3.2 changelog lists the smaller fixes that shipped alongside.
