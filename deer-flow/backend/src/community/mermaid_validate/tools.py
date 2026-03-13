"""Mermaid diagram validation tool.

Extracts mermaid code blocks from markdown and validates each one using
the Mermaid CLI (``mmdc``) or a lightweight Node.js subprocess.  Falls back
to a Python regex heuristic when Node is not available.
"""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from langchain.tools import tool

_MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)

_NODE_VALIDATE_SCRIPT = """\
const mermaid = require("mermaid");
mermaid.initialize({ startOnLoad: false, suppressErrorRendering: true });
const src = require("fs").readFileSync(process.argv[2], "utf-8");
mermaid.parse(src)
  .then(() => console.log(JSON.stringify({ ok: true })))
  .catch(e => console.log(JSON.stringify({ ok: false, error: String(e.message || e) })));
"""


def _find_node() -> str | None:
    """Return the path to a ``node`` binary, or ``None``."""
    return shutil.which("node")


def _find_mermaid_module() -> str | None:
    """Try to locate an installed ``mermaid`` npm module."""
    try:
        result = subprocess.run(
            ["node", "-e", "console.log(require.resolve('mermaid'))"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _validate_with_node(diagram: str) -> dict:
    """Validate a single diagram via Node.js + mermaid."""
    with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", delete=False) as f:
        f.write(diagram)
        diagram_path = f.name

    script_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".cjs", mode="w", delete=False) as sf:
            sf.write(_NODE_VALIDATE_SCRIPT)
            script_path = sf.name

        result = subprocess.run(
            ["node", script_path, diagram_path],
            capture_output=True,
            text=True,
            timeout=15,
        )

        stdout = result.stdout.strip()
        if stdout:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                pass

        if result.returncode != 0:
            error_text = (result.stderr or result.stdout or "unknown error").strip()
            return {"ok": False, "error": error_text}

        return {"ok": True}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Validation timed out"}
    except Exception as e:
        return {"ok": False, "error": f"Validation subprocess error: {e}"}
    finally:
        Path(diagram_path).unlink(missing_ok=True)
        if script_path:
            Path(script_path).unlink(missing_ok=True)


# Common syntactic patterns that cause Mermaid parse errors.
_HEURISTIC_CHECKS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bdate\s*:\s*\d+\.\d+", re.IGNORECASE), "Invalid date value (numeric with decimal). Use YYYY-MM-DD or a categorical label."),
    (re.compile(r"\bdate\s*:\s*\d{1,3}\b", re.IGNORECASE), "Possibly invalid short date value. Use YYYY-MM-DD or a categorical label."),
    (re.compile(r"[^\x00-\x7F]"), "Non-ASCII characters detected — may cause parser errors depending on context."),
]


def _validate_with_heuristics(diagram: str) -> dict:
    """Best-effort Python-only validation using regex heuristics."""
    errors: list[str] = []
    for pattern, message in _HEURISTIC_CHECKS:
        if pattern.search(diagram):
            errors.append(message)

    if errors:
        return {"ok": False, "error": "; ".join(errors), "method": "heuristic"}
    return {"ok": True, "method": "heuristic"}


def _validate_diagram(diagram: str, use_node: bool) -> dict:
    if use_node:
        return _validate_with_node(diagram)
    return _validate_with_heuristics(diagram)


def extract_mermaid_blocks(markdown: str) -> list[str]:
    """Return all mermaid code blocks found in *markdown*."""
    return _MERMAID_BLOCK_RE.findall(markdown)


@tool("validate_mermaid_syntax", parse_docstring=True)
def validate_mermaid_syntax_tool(mermaid_code: str) -> str:
    """Validate one or more Mermaid diagrams and return structured error reports.

    Accepts either:
    - A single Mermaid diagram (raw syntax, no code fences).
    - A full Markdown string containing one or more ```mermaid``` blocks.

    If ANY diagram is invalid, fix the syntax and call this tool again before
    presenting the content to the user.

    Args:
        mermaid_code: Raw Mermaid syntax OR Markdown containing ```mermaid``` blocks.
    """
    blocks = extract_mermaid_blocks(mermaid_code)
    if not blocks:
        blocks = [mermaid_code.strip()]

    node_available = _find_node() is not None and _find_mermaid_module() is not None

    results: list[dict] = []
    all_ok = True
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue
        result = _validate_diagram(block, use_node=node_available)
        result["diagram_index"] = i
        result["diagram_preview"] = block[:120] + ("..." if len(block) > 120 else "")
        results.append(result)
        if not result.get("ok"):
            all_ok = False

    response: dict = {
        "ok": all_ok,
        "total_diagrams": len(results),
        "valid_count": sum(1 for r in results if r.get("ok")),
        "invalid_count": sum(1 for r in results if not r.get("ok")),
        "validation_method": "node+mermaid" if node_available else "heuristic",
        "results": results,
    }

    if not all_ok:
        response["recommendation"] = (
            "Fix the invalid diagram(s) and call validate_mermaid_syntax again. "
            "If you cannot fix the syntax, replace the diagram with a Markdown table."
        )

    return json.dumps(response, ensure_ascii=False, indent=2)
