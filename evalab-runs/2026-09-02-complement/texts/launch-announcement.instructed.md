# Dark mode is here

Dark mode shipped today in version 3.2, on iOS, Android, web, and desktop. Turn it on under Settings → Appearance.

The obvious version of this feature is to invert the colors and call it done. That produces pure white text on pure black, which most people find hard to read for long stretches because the contrast edge bleeds. So the background is a near-black at #16161a and body text sits at 87% opacity. Contrast ratios land between 8:1 and 14:1 depending on the element, above the WCAG AA floor of 4.5:1.

Code blocks, quotes, and highlight colors were the hard part. The seven highlighter shades from light mode are unreadable against a dark background at their original saturation, so each one was remapped by hand rather than run through an algorithm. A yellow highlight in a dark note is now a muted amber. Your existing notes keep their highlight assignments; only the rendered color changes.

There is an automatic setting that follows your system theme, including scheduled switching if your OS does sunset-to-sunrise. If you want dark mode always on regardless of what the rest of your machine is doing, pick "Always dark" instead of "System."

Two known gaps. Exported PDFs still render in light mode, since a dark PDF wastes ink when printed; a toggle for that is planned for 3.3. Embedded images with transparent backgrounds may look odd against dark surfaces, and there is no fix for that yet beyond adding your own background.

Bug reports go to support@example.com or the in-app feedback form.
