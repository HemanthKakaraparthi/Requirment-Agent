"""
Requirement Agent — CLI runner
Runs Phase 1 (PRD generation) as a standalone agent.

Usage:
    cd requirement-agent
    python main.py
"""

import re
import sys
import json
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from langchain_core.callbacks import BaseCallbackHandler
from agent import build_agent, SP_STATUS, _SP_ENABLED
from tools import (
    save_prd as _save_prd,
    load_product_context as _load_ctx,
    list_existing_prds as _list_prds,
)
RAG_ENABLED = False
RAG_STATUS = "not applicable (Phase 1)"

_RAW_JSON_RE = re.compile(r'^\s*\{')

console = Console()


def _intercept_raw_save(output_text: str) -> dict | None:
    """
    The ASIMOV proxy can't handle large save_prd payloads as structured tool calls.
    Detect when the LLM returns the tool call as plain JSON text and execute it directly.
    """
    text = output_text.strip()
    if not text.startswith("{"):
        return None
    try:
        raw = json.loads(text)
    except Exception:
        return None

    name = raw.get("name", "")
    args = raw.get("arguments", raw)

    if "save_prd" in name or "prd_json" in args:
        pj = args.get("prd_json", "")
        if not pj:
            return None
        try:
            result_str = _save_prd.func(pj)
            data = json.loads(result_str)
        except Exception as e:
            return {"output": f"❌ Direct save failed: {e}"}

        if data.get("saved"):
            jp = data.get("json_path", "")
            mp = data.get("md_path", "")
            console.print(f"[bold green]\\[saved JSON][/bold green] {jp}")
            console.print(f"[bold green]\\[saved MD]  [/bold green] {mp}")
            return {
                "output": (
                    f"✅ PRD saved.\n\n"
                    f"**JSON:** `{jp}`\n"
                    f"**Markdown:** `{mp}`"
                )
            }
        return {"output": f"❌ Save failed: {data.get('error', 'unknown error')}"}

    return None


class ToolEchoHandler(BaseCallbackHandler):
    def on_tool_end(self, output, **kwargs) -> None:
        try:
            data = json.loads(output) if isinstance(output, str) else None
        except Exception:
            return
        if not isinstance(data, dict):
            return
        if "error" in data:
            console.print(f"[bold red]\\[tool error][/bold red] {data['error']}")
            if "hint" in data:
                console.print(f"[yellow]hint:[/yellow] {data['hint']}")
            return
        if data.get("saved") is True:
            jp = data.get("json_path")
            mp = data.get("md_path")
            if jp:
                console.print(f"[bold green]\\[saved JSON][/bold green] {jp}")
            if mp:
                console.print(f"[bold green]\\[saved MD]  [/bold green] {mp}")


def print_banner():
    console.print(Panel(
        Text.assemble(
            ("  Requirement Agent", "bold cyan"), "\n",
            ("  TestOps — SDLC Agent Pipeline\n", "dim"), "\n",
            ("  Idea / File  →  PRD", "green"),
        ),
        border_style="cyan",
        padding=(0, 2),
    ))

    if _SP_ENABLED:
        console.print(f"[bold green]\\[SharePoint {SP_STATUS}][/bold green]")
    else:
        console.print(f"[dim]\\[SharePoint {SP_STATUS}][/dim]")

    if RAG_ENABLED:
        console.print(f"[bold cyan]\\[RAG {RAG_STATUS}][/bold cyan]")
    else:
        console.print(f"[dim]\\[RAG {RAG_STATUS}][/dim]")

    console.print("[dim]Type 'quit' to exit.[/dim]\n")


async def _amain():
    print_banner()

    try:
        executor = build_agent()
    except Exception as e:
        console.print(f"[bold red]Failed to initialise agent:[/bold red] {e}")
        sys.exit(1)

    # Pre-warm: inject product context + PRD list into memory so the LLM
    # never needs to call those tools itself (avoids multi-tool bundling at startup).
    try:
        _ctx_raw  = _load_ctx.func("load")
        _prd_raw  = _list_prds.func("list")
        executor.memory.save_context(
            {"input": "Load product context and list existing PRDs."},
            {"output": (
                f"✅ Product context loaded.\n\n"
                f"Existing PRDs in local store:\n{_prd_raw}"
            )},
        )
        console.print("[dim]\\[context pre-loaded][/dim]")
    except Exception as _e:
        console.print(f"[dim]\\[context pre-load failed: {_e}][/dim]")

    callbacks = [ToolEchoHandler()]

    console.print(
        "\n[bold cyan]Agent:[/bold cyan] Hi! I'm the TestOps Requirement Agent. "
        "I can write a PRD from a brief, idea, or file. "
        "Just tell me what you'd like to build!\n"
    )

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break

        try:
            result = await executor.ainvoke(
                {"input": user_input},
                config={"callbacks": callbacks},
            )

            output_text = result.get("output", "") if isinstance(result, dict) else str(result)
            for _retry in range(2):
                if not _RAW_JSON_RE.search(output_text):
                    break

                intercepted = _intercept_raw_save(output_text)
                if intercepted is not None:
                    result = intercepted
                    output_text = result.get("output", "")
                    break

                console.print("[dim]\\[retrying — model returned raw JSON instead of tool call][/dim]")
                try:
                    _raw = json.loads(output_text.strip().split("\n")[0])
                    _name = _raw.get("name", "").split(".")[-1]
                    _tool_hint = f"Call the `{_name}` tool now — ONE tool only, wait for its result." if _name else ""
                except Exception:
                    _tool_hint = ""

                _retry_msg = _tool_hint or (
                    "Your last response was raw JSON text, not an actual tool call. "
                    "Use the tools directly — call ONE tool at a time and wait for its result."
                )
                result = await executor.ainvoke(
                    {"input": _retry_msg},
                    config={"callbacks": callbacks},
                )
                output_text = result.get("output", "") if isinstance(result, dict) else str(result)

            text = result["output"] if isinstance(result, dict) and "output" in result else str(result)
            console.print(f"\n[bold cyan]Agent:[/bold cyan] {text}\n")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}\n")
            console.print(f"[dim]Input was:[/dim] {user_input[:120]}\n")


def main():
    try:
        asyncio.run(_amain())
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass


if __name__ == "__main__":
    main()
