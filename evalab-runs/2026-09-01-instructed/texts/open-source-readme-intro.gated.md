Most charting libraries make the easy chart easy and the strange one impossible. Bar chart? Four lines. Then you need a log-scaled second axis, three annotation rules, and a shaded band behind all of it, and now it's 1am and you're reading the source to work out which of eleven nested config objects owns the tick formatter. The library had an opinion about which charts exist, and yours wasn't on the list.

Sketchpad has one idea. A scale maps data to pixels; a mark draws using scales. Bars, lines, points, areas, and anything you write yourself are the same kind of object, so composing them means putting them in a list. There is no chart-type enum to outgrow. It ships as `<BUNDLE_SIZE>` gzipped with `<DEPENDENCY_COUNT>` dependencies, and the same mark code renders to SVG or Canvas.

It also doesn't own your DOM. You hand it a node, it draws into it, and it cleans up after itself.

The trade is real. A `<POINT_COUNT>`-point scatter draws in `<RENDER_MS>` on `<REFERENCE_MACHINE>`, but `<OMITTED_FEATURE_1>`, `<OMITTED_FEATURE_2>`, and `<OMITTED_FEATURE_3>` are not in the box. Those live in separate packages, or in your own repo. This one stays small. MIT licensed, and it works with React, Vue, Svelte, or nothing at all.
