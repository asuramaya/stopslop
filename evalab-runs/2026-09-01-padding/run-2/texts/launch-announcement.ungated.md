Written with the human-prose skill's checklist. The app name and all specifics are invented placeholders — swap in your real numbers before publishing.

---

**Dark mode is live in Notebase 3.4**

We shipped dark mode today. It took longer than it should have, and here's why.

The first version was done in a week: invert the palette, ship it. Then someone opened a note with three code blocks and a table, at night, and the whole thing glowed. Pure black backgrounds make white text smear on OLED screens. Syntax highlighting tuned for a white page turns into neon. So we threw that build out and started again from the text.

The palette we kept is built on a #16181C surface, not black, with body text at #E4E6EA — a contrast ratio of 13.2:1, comfortably past the WCAG AA floor of 4.5. Every accent got re-picked by hand against the dark surface instead of dimmed down from the light theme: links, inline code, quote rules, and the yellow of a highlighter mark.

What you can change:

- Follow the system theme, or pin light or dark per device.
- Schedule the switch at sunset. It uses your device's location, which stays on the device.
- Leave images at full brightness, or dim them to 80% so a screenshot doesn't blind you at 1 a.m.

Exported PDFs stay light. That surprised two beta testers, so it's now a toggle in Settings → Appearance.

Out now in 3.4 on iOS, Android, and web. Desktop follows next week — one stubborn bug in the editor's find bar is holding it.

Something look wrong? Tell us: feedback@notebase.app
