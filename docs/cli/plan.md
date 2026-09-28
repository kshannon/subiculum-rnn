# CLI implementation plan

Read with spec.md. No code here.

## Architecture

    src/subiculum_rnn/
      paths.py         configs_dir(): the checkout containing the package
      store.py         resolve_store(flag) -> Store: flag, then SUBICULUM_RNN_STORE, then artifacts/
                       Store: root, kind_dir(kind), marker read/write, init(), check()
      experiments/registry.py   list_manifests(dir) unchanged; id allocation lands with the first writer
      cli/
        __init__.py    build_parser(), main(): global options, group registration, dispatch
        _output.py     table(), lines(), emit(data, as_json), fail(message, code)
        _parsers.py    group(), leaf(): help from docstrings, example epilogs; add_json(), add_dry_run()
        _stub.py       not_implemented(command, spec_section): message to stderr, exit 3
        store.py       register(groups); init_store(), inspect_store()
        env.py         register(groups); list_envs(), inspect_env()
        agent.py       register(groups); stubs
        data.py        register(groups); list (real), stubs
        model.py       register(groups); list (real), stubs
        analysis.py    register(groups); stubs
        experiment.py  register(groups); list (real), stubs

Every group module has the same shape: a one-line HELP string, a `register`
function that adds the group's subparsers and binds each leaf to a command
function through a small adapter, and one plain function per command taking
the resolved store plus explicit typed arguments and returning an exit code.
Docstrings are the help text; each leaf parser carries a one-line example as
its epilog. The adapter is the only place that reads an argparse namespace,
so command functions are plain Python and reusable from notebooks.

The store is package code, not CLI code: `store.py` owns resolution order,
the marker file, layout creation and the consistency check, so notebooks and
future writers use the same object the CLI does. Real data has no
representation anywhere in this layout.

## Implementation order

1. Package skeleton and output helpers. Move env list and inspect across with
   behavior unchanged; existing CLI tests pass. Delete the old module.
2. Store: `store.py` with resolution order, marker, init and check, then the
   `store` group and the `--store` global replacing `--root`. Data list and
   experiment list read from the store. Tests cover precedence, refusal
   without a marker, init layout, inspect counts.
3. Help and exit-code contract: descriptions and examples on every leaf, the
   stub helper, codes 1 through 3 exercised.
4. Group modules with stubs: agent, data, model, analysis, experiment. Every
   command parses its full argument list, including `--json` and `--dry-run`.
5. Tests: a walk over the parser tree asserting every leaf has a description
   and an example; every stub exits 3; bad arguments exit 2.
6. Docs: README setup with the store and the environment variable, an
   explanation of how synthetic data is generated, reproduction commands,
   tasks checked off.

## Key decisions

- argparse over Typer. Zero dependencies. Readability comes from structure,
  one function per command with explicit parameters, not from the framework.
  Revisit if any group module passes 150 lines.
- One module per group so the help tree mirrors the file tree.
- Two locations, not one: configs from the checkout, artifacts from a store
  chosen by flag, environment variable, or default. `--root` goes away.
- A store is marked. Writers refuse unmarked directories so an unmounted
  drive or a typo cannot produce a stray tree.
- Ids are derived from directories, never from an index file that can drift.
  A uuid and the input hash in every manifest give identity across stores.
- Stubs parse real arguments now so the help contract and tests are complete
  before the science exists, and later work only replaces function bodies.
- Recordings and analysis results live inside the model directory, keeping
  three artifact kinds and one registry.
- Exit code 4 is reserved now and first used when a consumer command lands.
- The existing single-file CLI is replaced, not kept alongside.
