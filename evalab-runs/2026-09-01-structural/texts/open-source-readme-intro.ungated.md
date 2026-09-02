# Strata

Strata draws charts. That's it: no dashboard framework, no state manager, no opinion about how you fetch your data.

Most charting libraries make you pick a side. Either you take the high-level wrapper with twelve chart types and a config object that runs out of room the moment you need a second y-axis, or you take D3 and a week of your life. Strata sits between them. You get primitives — scales, axes, marks — and a dozen ready-made chart types composed from those same primitives. When the ready-made version stops fitting your case, you drop one layer down instead of starting over in a different library.

It ships as ESM, weighs 14 kB gzipped, has no runtime dependencies, and renders to SVG or Canvas from identical code. Server-side rendering works, because nothing touches `document` until you ask for interaction.

Accessibility is on by default. Every chart emits a table fallback and keyboard-navigable data points; turning that off takes a flag.

MIT licensed. Running in production at Hallow Labs since March 2026.

---

Two things to fill in before you publish: the bundle size and the production reference are placeholders — swap in your real numbers, or cut the last line rather than ship a claim you can't back.
