"""agent: behavioral profiles (model rats) from configs/agents/."""

from ._parsers import add_json, group, leaf
from ._stub import not_implemented

HELP = "behavioral agents (model rats)"
DESCRIPTION = ("An agent is a behavioral profile declared in configs/agents/: "
               "speed, turning and dwell parameters and a goal policy, with a "
               "content hash. Datasets record which agents produced them, so an "
               "agent can be traced to every result it touched. Here, agent "
               "means model rat.")


def register(groups) -> None:
    commands = group(groups, "agent", HELP, DESCRIPTION)

    p = leaf(commands, "list", list_agents, example="subiculum-rnn agent list",
             stub=True)
    add_json(p)
    p.set_defaults(run=lambda a: list_agents(as_json=a.json))

    p = leaf(commands, "inspect", inspect_agent,
             example="subiculum-rnn agent inspect ballistic_runner", stub=True)
    p.add_argument("agent_id", metavar="<agent>",
                   help="config name under configs/agents/")
    add_json(p)
    p.set_defaults(run=lambda a: inspect_agent(a.agent_id, as_json=a.json))


def list_agents(*, as_json: bool = False) -> int:
    """List every agent config with its hash, headline statistics and use counts.

    Reads: configs/agents/*.yaml and every manifest in the store.
    Writes: nothing.
    """
    return not_implemented("agent list", "Commands")


def inspect_agent(agent_id: str, *, as_json: bool = False) -> int:
    """Describe one agent: parameters, current and superseded hashes, references.

    Reads: configs/agents/<agent>.yaml and every manifest in the store.
    Writes: nothing.
    """
    return not_implemented("agent inspect", "Commands")
