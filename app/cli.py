from __future__ import annotations

from datetime import datetime, timedelta, timezone

import typer

from app.models import ResearchRunRequest, RunMode
from app.service import ResearchService


app = typer.Typer(help="Generate evidence-grounded AI finance research reports.")


@app.callback()
def main() -> None:
    """AI Finance Research Agent command line interface."""


def _parse_since(value: str) -> timedelta:
    normalized = value.strip().lower()
    if normalized.endswith("h"):
        return timedelta(hours=float(normalized[:-1]))
    if normalized.endswith("d"):
        return timedelta(days=float(normalized[:-1]))
    raise typer.BadParameter("--since must end in 'h' or 'd', for example 24h or 7d")


@app.command()
def run(
    topic: str = typer.Option(..., help="Research topic"),
    since: str = typer.Option("7d", help="Lookback period such as 24h or 7d"),
    mode: RunMode = typer.Option(
        RunMode.REPLAY,
        help="replay, replay_llm, or live",
    ),
    max_events: int = typer.Option(8, min=5, max=10),
) -> None:
    end_time = datetime.now(timezone.utc)
    request = ResearchRunRequest(
        topic=topic,
        start_time=end_time - _parse_since(since),
        end_time=end_time,
        max_events=max_events,
        mode=mode,
    )

    def observer(stage: str, payload: dict) -> None:
        status = payload.get("status", "")
        typer.echo(f"[{stage}] {status}")

    try:
        result = ResearchService().run(request, observer=observer)
    except Exception as exc:
        typer.echo(f"Run failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Run ID: {result.run_id}")
    typer.echo(f"Sources: {len(result.sources)}; Events: {len(result.events)}")
    typer.echo(
        "RSS sources: "
        f"total={result.metrics.get('rss_source_total', 0)}, "
        f"success={result.metrics.get('rss_source_success', 0)}, "
        f"failed={result.metrics.get('rss_source_failed', 0)}"
    )
    typer.echo(
        "Articles: "
        f"collected={result.metrics.get('collected_count', 0)}, "
        f"deduplicated={result.metrics.get('deduplicated_count', 0)}"
    )
    group_coverage = result.metrics.get("rss_group_coverage", {})
    if group_coverage:
        typer.echo(
            "RSS groups: "
            + ", ".join(
                f"{group}={values['successful']}/{values['configured']}"
                for group, values in group_coverage.items()
            )
        )
    typer.echo(f"Markdown: {result.artifacts.markdown_report_path}")
    typer.echo(f"HTML: {result.artifacts.html_report_path}")
    typer.echo(f"JSON: {result.artifacts.result_json_path}")


if __name__ == "__main__":
    app()
