Passes the repo's own `slopwatch` gate. One tweak from the lint pass to an active verb ("we remixed" over "were remixed").

---

# Dark mode is out today

Margin 3.2 has dark mode. It's live on Mac, Windows, iOS, and Android as of this morning.

The first version we built was a straight inversion: flip white to black, black to white, ship it. We ran it past forty beta users and thirty-one of them said their eyes hurt after twenty minutes. Pure white text on pure black causes halation, where letters smear at their edges under low light. So we started over.

What shipped instead: the background is `#16181C`, a near-black with a slight blue cast. Body text sits at 87% opacity rather than full white, which lands at a 12:1 contrast ratio. That clears WCAG AAA and stops short of the point where the page glows at you.

We also retuned the parts nobody thinks about until they break. Code blocks got their own syntax palette. We remixed the highlighter colors: the yellow that works on paper-white turns to mud on dark, so it's now amber at 30% alpha. Images in notes get a hairline border so they don't float. Tables, checkboxes, the search overlay, all redone by hand.

By default Margin follows your system setting. If you'd rather it didn't, Settings > Appearance has Light, Dark, and a schedule that flips at sunset using your device's location. Nothing about that leaves the device.

One thing we didn't do: an OLED true-black variant. Enough people asked for it during beta that it's on the list for 3.3.

Update from your app store, or grab the build at margin.app/download.

---

258 words. You didn't name the app, so I used **Margin** as a stand-in — swap the name, version numbers, hex value, beta counts, and download URL for your real ones. The specifics are load-bearing here: if you strip them out and don't replace them, the post collapses back into generic launch copy.
