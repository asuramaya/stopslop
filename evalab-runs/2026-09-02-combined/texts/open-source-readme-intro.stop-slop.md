# Kettle

Kettle turns an array of objects into an SVG chart. Give it rows, then name the field for each axis:

```js
import { line } from 'kettle'
line(data, { x: 'month', y: 'revenue' }).mount('#chart')
```

You get a line chart with axes and a legend. You do not need a theme file or a build step.

Kettle covers 11 chart types in 14kB gzipped, with no dependencies, so `npm install kettle` adds one package to your lockfile. The output is SVG you can open in devtools and style with CSS, since every bar and axis carries the class names you pass in.

We wrote Kettle after losing two days to a stacked bar chart that took 200 lines of configuration elsewhere. Here you reach for the config object when you want to change something. Defaults handle the rest.

Kettle runs in the browser and in Node, where it hands back an SVG string you can write to disk or drop into an email. The React and Svelte wrappers live in this repo under `packages/`.

New to it? Start with the 5-minute tutorial. If you would rather see the full surface first, the API reference fits on two pages.
