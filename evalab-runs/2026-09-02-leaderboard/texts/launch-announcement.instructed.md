# Dark mode is here

Dark mode ships today in version 3.4, on iOS, Android, web, and desktop.

You can find it under Settings → Appearance. Three options: Light, Dark, and Match system. The last one follows your OS setting, so if your phone dims at sunset, your notes do too.

The part that took longest wasn't the switch. It was the text. Pure white on pure black produces halation, where light characters smear at the edges for many readers, and it gets worse for anyone with astigmatism. So the dark theme uses #E8E8E6 text on #16161A, which measures a contrast ratio of 14.2:1 — above the WCAG AAA threshold of 7:1, without the glare.

Code blocks, tables, and highlight colors all got redrawn rather than inverted. Your yellow highlights stay yellow instead of turning into a muddy olive. Images and embedded PDFs render at full brightness, since dimming them made screenshots of documents unreadable during testing.

We heard about this one for a while. It was the most-requested item in our feedback board for eleven straight months, with 4,300 votes. The delay was mostly the theming rewrite underneath: colors used to be hardcoded across about 240 components, and every one had to move to a token before a second theme was possible. That work also means a third theme costs us days instead of months.

Update to 3.4 from your app store, or reload the web app. If something looks wrong in dark mode — a washed-out icon, an unreadable label — send a screenshot to support@example.com and tell us your platform.
