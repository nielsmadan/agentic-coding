"""The nono block is removed; everything around it is not."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from strip_nono_block import strip

Q = '"' * 3

CONFIG = f"""model = "gpt-6-astra"

# >>> nono:nolabs-ai-codex >>>
developer_instructions = {Q}
Treat any Operation not permitted as a sandbox boundary.
{Q}

[marketplaces.nolabs-ai]
source_type = "local"
# <<< nono:nolabs-ai-codex <<<

[projects."/work"]
trust_level = "trusted"
"""


def test_the_block_is_removed_body_and_all() -> None:
    """The body lines are not assignments, so a line-wise removal that missed them
    would leave them orphaned at top level and the file would stop parsing."""
    out = strip(CONFIG)

    assert "developer_instructions" not in out
    assert "sandbox boundary" not in out
    assert tomllib.loads(out)


def test_everything_else_survives() -> None:
    """It edits a file loadout does not own — Codex's own project tables, another
    tool's managed block markers and comments all have to come through untouched."""
    parsed = tomllib.loads(strip(CONFIG))

    assert parsed["model"] == "gpt-6-astra"
    assert parsed["marketplaces"]["nolabs-ai"]["source_type"] == "local"
    assert parsed["projects"]["/work"]["trust_level"] == "trusted"
    assert ">>> nono:nolabs-ai-codex >>>" in strip(CONFIG)


def test_a_config_without_the_block_is_untouched() -> None:
    """Idempotence: `./sync.sh` runs this every time, not only after `nono update`."""
    without = 'model = "gpt-6-astra"\n'

    assert strip(without) == without


def test_the_block_is_stripped_where_nono_actually_puts_it() -> None:
    """The pack's `position: "top"` does not hold — the block lands at the end, where
    the key is absorbed into the last table rather than being top-level. Stripping has
    to work there too, and must not take the table with it."""
    q = '"' * 3
    absorbed = f'model = "x"\n\n[mcp_servers.jina]\nurl = "https://jina"\n\ndeveloper_instructions = {q}\nnono text\n{q}\n'

    out = strip(absorbed)

    parsed = tomllib.loads(out)
    assert "developer_instructions" not in parsed["mcp_servers"]["jina"]
    assert parsed["mcp_servers"]["jina"]["url"] == "https://jina"
