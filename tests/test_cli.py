from typer.testing import CliRunner

from app.cli import app


def test_cli_replay_smoke():
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--topic",
            "AI Agent",
            "--since",
            "24h",
            "--mode",
            "replay",
            "--max-events",
            "5",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Sources: 14; Events: 5" in result.output
    assert "Markdown:" in result.output

