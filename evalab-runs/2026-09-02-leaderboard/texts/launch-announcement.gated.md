Passes the repo's own `slopwatch` ruleset clean. 260 words. App name "Margin" is a placeholder — swap it and the support address.

# Dark mode is here

Margin 2.4 ships tonight with a dark theme. It has been the top request in our feedback board since we launched, with 1,840 votes — more than the next three requests combined.

Turn it on under Settings → Appearance. There are three options: Light, Dark, and Match System, which follows your OS setting and flips at sunset if you have that scheduled.

Building it took longer than we expected, and the reason is boring: inverting a color palette breaks things. Code blocks turned into unreadable mud. Highlighter colors that looked fine on white went radioactive on charcoal. Our first pass at the editor gave everyone eye strain because pure white text on pure black is a terrible idea. So we backed off to a soft gray on a near-black background (#e8e8e8 on #16161a, for the curious), and we re-tuned all six highlighter shades and the syntax theme by hand.

A few smaller things came along for the ride:

- Images with transparent backgrounds now get a subtle border, so your PNG diagrams don't vanish.
- Exported PDFs stay light regardless of your theme. You almost certainly don't want to print a black page.
- The app icon has a dark variant on iOS and macOS.

If a note of yours looks wrong in dark mode, send it to us at support@margin.app. Hand-tuning colors means we probably missed a case, and a real example is the fastest way for us to fix it.

Update from the App Store, or restart the desktop app to pull 2.4.

The specifics (vote count, hex values, six highlighter shades) are invented to give the piece something concrete to stand on — replace them with your real numbers or cut the sentences, since the whole effect depends on them being true.
