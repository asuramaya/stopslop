**Dark mode ships today**

We shipped dark mode. It took embarrassingly long.

The delay wasn't taste, it was the editor. Notes render whatever you put in them: pasted screenshots, code blocks, tables copied out of email with hardcoded white backgrounds. Inverting a theme is easy. Inverting one without turning your three-year-old recipe note into gray-on-gray took four rewrites of the style layer.

What's in it:

Three themes — Light, Dark, and System, which follows your OS setting. Toggle with Cmd+Shift+D, or Ctrl+Shift+D on Windows.

The dark palette isn't pure black. The background sits at #16171A, around 8% lightness, because true black on OLED makes text edges shimmer while you scroll. If you want the battery savings anyway, flip "OLED black" under Appearance.

Pasted images keep their own background. We detect white-matted PNGs and draw a thin border around them instead of letting them glow like a flashlight in a dark room.

Syntax highlighting got its own palette, tuned so every token color clears 4.5:1 contrast. Links too. Those were the worst thing in the beta — our default blue came in at 2.9:1 and people told us, repeatedly.

Export still renders light. A PDF you send a colleague shouldn't arrive wearing your theme.

Live now in 3.4 on macOS, Windows, iOS, and Android. Web lands next week, once a service worker fix clears review.

If something looks broken in the dark, tell us. Screenshots help more than descriptions.

---

~250 words. The version number, hex value, contrast ratios, and shortcut are placeholders — swap in your real ones, since the specifics are what keep it from reading like generic launch copy.
