This roadmap covers the next two quarters of work on the CLI, the API, and the editor integrations. It's public because the plans affect how you build: a breaking change to the config format, a new authentication flow, a CLI command that replaces three older ones.

Three things drive the priorities below. First, startup time. The tool takes too long to load on large monorepos, and the profiling work this quarter targets the plugin resolution step specifically. Second, the API surface has grown past what our docs cover well, so we're splitting the reference into a stable core and an experimental namespace, with clear rules for what can change without notice. Third, editor support has lagged behind the CLI. VS Code gets parity with CLI flags this quarter; JetBrains support starts after that.

Dates here are targets, not commitments. Some items will slip, some will get cut, and we'll update this page when that happens rather than quietly dropping them. If something you rely on isn't listed, check the issue tracker before assuming it's off the roadmap; a lot of small fixes happen outside this document.

Feedback on any of this goes to the usual GitHub discussions thread, and we read all of it.
