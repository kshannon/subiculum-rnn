# CLI tasks

Atomic, in order, each verified by `pixi run test` plus the listed command.
Spec sections in brackets.

- [x] T1 Create the `cli/` package: `_output.py` (table, lines, emit, fail) and
  `__init__.py` (build_parser, main, `--version`). Move env list and inspect into
  `cli/env.py` with behavior unchanged. Delete `cli.py`.
  Verify: existing CLI tests pass; `subiculum-rnn env list`. [Commands, Non-Functional]
- [x] T2 `store.py` in the package: `resolve_store` with precedence flag, environment
  variable, default; `Store` with kind directories, marker read and write, `init`,
  `check`. Tests: precedence, refusal without marker, init creates layout and marker,
  check reports an id that differs from its directory. [Data Model, Edge Cases]
- [x] T3 `cli/store.py`: `store init [DIR]` and `store inspect [--json]`; `--store` global
  replaces `--root`; data list and experiment list read from the store; tests updated
  to pass `--store`. Verify: `subiculum-rnn store init /tmp/s && subiculum-rnn --store /tmp/s store inspect`. [Commands, Global options]
- [x] T4 Help contract: description on every group and command, one-line example
  epilog on every leaf, docstrings as help. Test walks the parser tree.
  Verify: `subiculum-rnn env inspect --help` shows reads, writes, example. [Behavior]
- [x] T5 Exit codes: no command 1, unknown name 2, unusable store 2,
  `_stub.not_implemented` 3 with a message naming the spec section. One test each. [Behavior]
- [x] T6 `cli/agent.py`: list and inspect stubs, `--json` accepted. [Commands]
- [x] T7 `cli/data.py`: inspect, generate, validate (`--reference <file>`), stats stubs
  with full arguments; `--dry-run` on generate and validate. [Commands]
- [x] T8 `cli/model.py`: list, inspect, train, evaluate stubs; `--dry-run` on train and
  evaluate. [Commands]
- [x] T9 `cli/analysis.py`: record-hidden and axis stubs, `--dry-run`. [Commands]
- [x] T10 `cli/experiment.py`: inspect, run, reproduce stubs; `--dry-run` on run and
  reproduce. [Commands]
- [x] T11 Parser-tree test: every leaf parses its documented arguments; every list and
  inspect accepts `--json`; every writer accepts `--dry-run`; every stub exits 3. [Commands, Edge Cases]
- [x] T12 Docs: README setup (store init, environment variable) and an explanation of how
  synthetic data is generated; `docs/reproduction.md` commands; this list checked off. [all]

## Done, 2026-09-28

All twelve tasks landed as one commit each on `feature/cli`. Deviations from
the plan, kept small and recorded here:

- A second helper module, `cli/_parsers.py`, holds the docstring-to-help
  machinery and the shared `--json` and `--dry-run` flags, beside `_output.py`.
- `model list` is real, not a stub: it is the same registry listing as data
  and experiment list, so a stub would have been artificial.
- T4 (help contract) and T11 (parser tree) passed on first run: T1 had already
  put reads, writes and an example on every command. They stand as guards for
  every group added since and any added later.
- Stubs do not touch the store, so `data generate` and friends exit 3 even
  without a marker; the store check moves into each body when it is written.
