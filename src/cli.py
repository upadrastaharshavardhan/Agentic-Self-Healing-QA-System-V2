"""
Rich CLI for running investigations and inspecting results.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box

from src.graph.workflow import compile_graph
from src.models.schemas import FailureEvent, TestMetadata, InvestigationStatus
from src.state import InvestigationState

app = typer.Typer(help="Agentic Self-Healing QA System CLI", add_completion=False)
console = Console()


def _print_diagnosis(diagnosis) -> None:
    if not diagnosis:
        console.print("[red]No diagnosis produced[/red]")
        return

    status_color = {
        InvestigationStatus.RESOLVED: "green",
        InvestigationStatus.ESCALATED: "yellow",
        InvestigationStatus.AWAITING_APPROVAL: "cyan",
        InvestigationStatus.ABORTED: "red",
        InvestigationStatus.IN_PROGRESS: "blue",
    }.get(diagnosis.status, "white")

    console.print(Panel(
        f"[bold]Status:[/bold] [{status_color}]{diagnosis.status.value}[/{status_color}]\n"
        f"[bold]Failure Type:[/bold] {diagnosis.failure_type.value}\n"
        f"[bold]Root Cause:[/bold] {diagnosis.selected_root_cause}\n"
        f"[bold]Confidence:[/bold] {diagnosis.confidence:.0%}\n"
        f"[bold]Message:[/bold] {diagnosis.final_message}",
        title="Final Diagnosis",
        border_style=status_color,
    ))

    if diagnosis.facts:
        console.print("\n[bold green]FACTS[/bold green]")
        for f in diagnosis.facts:
            console.print(f"  • {f}")

    if diagnosis.observations:
        console.print("\n[bold blue]OBSERVATIONS[/bold blue]")
        for o in diagnosis.observations:
            console.print(f"  • {o}")

    if diagnosis.inferences:
        console.print("\n[bold yellow]INFERENCES[/bold yellow]")
        for i in diagnosis.inferences:
            console.print(f"  • {i}")

    if diagnosis.recommendation:
        rec = diagnosis.recommendation
        console.print(Panel(
            f"[bold]Action:[/bold] {rec.action.value}\n"
            f"[bold]Risk:[/bold] {rec.risk_level.value}\n"
            f"[bold]Level:[/bold] {rec.healing_level.name}\n"
            f"[bold]Rationale:[/bold] {rec.rationale}\n"
            f"[bold]Requires Approval:[/bold] {rec.requires_approval}",
            title="Recommendation",
            border_style="magenta",
        ))

    if diagnosis.evidence_trail:
        table = Table(title="Evidence Trail", box=box.SIMPLE)
        table.add_column("Agent", style="cyan")
        table.add_column("Source")
        table.add_column("Summary")
        table.add_column("Conf", justify="right")
        for ev in diagnosis.evidence_trail:
            table.add_row(ev.agent, ev.source, ev.summary[:80] + ("…" if len(ev.summary) > 80 else ""), f"{ev.confidence:.0%}")
        console.print(table)


@app.command()
def investigate(
    message: str = typer.Option(..., "--message", "-m", help="Failure message"),
    test_name: str = typer.Option("example_test", "--test", "-t"),
    environment: str = typer.Option("qa", "--env", "-e"),
    stack: Optional[str] = typer.Option(None, "--stack"),
    dump_json: bool = typer.Option(False, "--json", help="Also dump full diagnosis as JSON"),
):
    """Run a full investigation against a simulated failure."""
    console.print(Panel("[bold]Agentic Self-Healing QA – Investigation Runner[/bold]", style="bold blue"))

    event = FailureEvent(
        test_id=f"test-{test_name}",
        failure_message=message,
        stack_trace=stack,
        test_metadata=TestMetadata(test_name=test_name),
        environment=environment,
    )

    initial_state: InvestigationState = {
        "failure_event": event,
    }

    graph = compile_graph()

    console.print("[dim]Running investigation graph…[/dim]")
    final_state = asyncio.run(graph.ainvoke(initial_state))

    diagnosis = final_state.get("final_diagnosis")
    _print_diagnosis(diagnosis)

    if dump_json and diagnosis:
        out = Path("diagnosis_output.json")
        out.write_text(diagnosis.model_dump_json(indent=2))
        console.print(f"\n[dim]Full diagnosis written to {out}[/dim]")


@app.command()
def demo():
    """Run three pre-canned realistic scenarios."""
    scenarios = [
        {
            "name": "Locator changed after frontend deploy",
            "message": "Error: locator 'button[data-testid=\"login-button\"]' not found",
        },
        {
            "name": "Transient timeout / flake",
            "message": "Timeout 30000ms exceeded while waiting for element to be visible",
        },
        {
            "name": "API 503 from payment service",
            "message": "Request failed with status 503 Service Unavailable – payment-service",
        },
    ]

    for i, sc in enumerate(scenarios, 1):
        console.rule(f"[bold]Scenario {i}: {sc['name']}[/bold]")
        event = FailureEvent(
            test_id=f"test-scenario_{i}",
            failure_message=sc["message"],
            test_metadata=TestMetadata(test_name=f"scenario_{i}"),
            environment="qa",
        )
        initial_state: InvestigationState = {"failure_event": event}
        graph = compile_graph()
        console.print("[dim]Running investigation graph…[/dim]")
        final_state = asyncio.run(graph.ainvoke(initial_state))
        diagnosis = final_state.get("final_diagnosis")
        _print_diagnosis(diagnosis)
        console.print()


@app.command()
def version():
    from src import __version__
    console.print(f"Agentic Self-Healing QA v{__version__}")


if __name__ == "__main__":
    app()
