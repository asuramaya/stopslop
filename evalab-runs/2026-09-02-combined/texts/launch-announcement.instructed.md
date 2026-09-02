# Dark mode is here

Dark mode ships today in version 3.4, on desktop and mobile.

It started as the most-requested item in our feedback board, with 1,840 votes over two years. We kept putting it off because a note-taking app is mostly text, and inverting text is harder than inverting a dashboard. Pure white on pure black smears at small sizes. Code blocks, highlight colors, and inline images all need separate treatment, or the whole page turns muddy.

So the palette is not an inversion. The background is a dark gray (#16181C) rather than black, which cuts halation around letterforms. Body text sits at #E4E6EB, roughly 13:1 contrast, above the WCAG AAA threshold of 7:1 for body copy. The six highlighter colors were re-picked by hand at lower saturation, so a yellow highlight over dark gray stays readable instead of glowing.

Images and PDFs embedded in notes are left alone. We tried dimming them and it made scanned documents look damaged.

To turn it on, open Settings and choose Appearance. There are three options: light, dark, and match system. Match system follows your OS setting and switches at whatever schedule you have configured there, including sunset-to-sunrise on macOS and iOS.

Two things are still missing. Custom themes beyond the two we ship are not in this release. And the web clipper renders clipped pages in their original colors, since rewriting arbitrary CSS reliably is a separate project.

If something looks wrong in dark mode, particularly in older notes with pasted formatting, send us a screenshot at support@ourapp.com.
