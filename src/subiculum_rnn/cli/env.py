"""env: environment geometry from configs/environments/."""

import math

from ..environments import list_environments, load_environment
from ..paths import ProjectPaths
from ._output import emit, fail, lines, table
from ._parsers import add_json, group, leaf

HELP = "environment geometry"
DESCRIPTION = ("Environments are parametric configs under configs/environments/. "
               "Each resolves to a geometry spec with a content hash that every "
               "dataset records.")


def register(groups) -> None:
    commands = group(groups, "env", HELP, DESCRIPTION)

    p = leaf(commands, "list", list_envs, example="subiculum-rnn env list")
    add_json(p)
    p.set_defaults(run=lambda a: list_envs(ProjectPaths.from_root(a.root),
                                           as_json=a.json))

    p = leaf(commands, "inspect", inspect_env,
             example="subiculum-rnn env inspect triple_t --json")
    p.add_argument("env_id", metavar="<env>", help="config name, e.g. triple_t")
    add_json(p)
    p.set_defaults(run=lambda a: inspect_env(ProjectPaths.from_root(a.root),
                                             a.env_id, as_json=a.json))


def _path_length(waypoints) -> float:
    return sum(math.dist(a, b) for a, b in zip(waypoints[:-1], waypoints[1:]))


def _named_lengths(paths: dict) -> str:
    return ", ".join(f"{k} ({_path_length(v):.2f} m)"
                     for k, v in sorted(paths.items())) or "none"


def list_envs(paths: ProjectPaths, *, as_json: bool = False) -> int:
    """List every environment config with its type, walls, routes and hash.

    Reads: configs/environments/*.yaml.
    Writes: nothing.
    """
    names = list_environments(paths.environments)
    if not names:
        print(f"no environment configs under {paths.environments}")
        return 0
    rows = []
    for name in names:
        spec = load_environment(name, paths.environments)
        rows.append({"name": spec.name, "type": spec.kind,
                     "room": f"{spec.room[0]:.2f} x {spec.room[1]:.2f} m",
                     "walls": len(spec.walls), "routes": len(spec.routes),
                     "hash": spec.hash})
    emit(rows, table(rows, ["name", "type", "room", "walls", "routes", "hash"]),
         as_json=as_json)
    return 0


def inspect_env(paths: ProjectPaths, env_id: str, *, as_json: bool = False) -> int:
    """Describe one environment: geometry summary, or the canonical spec as JSON.

    Reads: configs/environments/<env>.yaml and its base config, if any.
    Writes: nothing.
    """
    try:
        spec = load_environment(env_id, paths.environments)
    except FileNotFoundError as e:
        return fail(str(e))
    params = {k: v for k, v in spec.params.items() if k != "derived"}
    pairs = [
        ("config", paths.environments / f"{spec.name}.yaml"),
        ("type", spec.kind),
        ("room", f"{spec.room[0]:.2f} x {spec.room[1]:.2f} m"),
        ("params", params),
    ]
    if "derived" in spec.params:
        pairs.append(("derived", spec.params["derived"]))
    pairs += [
        ("boundary", f"polygon, {len(spec.boundary)} vertices" if spec.boundary
         else "room rectangle"),
        ("walls", len(spec.walls)),
        ("centerline", f"{len(spec.centerline)} segments"),
        ("routes", _named_lengths(spec.routes)),
        ("returns", _named_lengths(spec.returns)),
        ("reward sites", ", ".join(f"{k} ({p[0]:.3f}, {p[1]:.3f})"
                                   for k, p in spec.reward_sites.items()) or "none"),
    ]
    emit({**spec.canonical(), "hash": spec.hash},
         lines(f"{spec.name}  [{spec.hash}]", pairs), as_json=as_json)
    return 0
