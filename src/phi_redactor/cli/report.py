"""CLI command for generating HIPAA Safe Harbor compliance reports.

Usage::

    phi-redactor report                    # Print summary to stdout
    phi-redactor report --full             # Full detailed report
    phi-redactor report --output report.json  # Export to file
    phi-redactor report --session <id>     # Filter by session
"""

from __future__ import annotations

import json

import click


@click.command("report")
@click.option("--full", is_flag=True, help="Generate a full detailed compliance report.")
@click.option("--output", "-o", type=click.Path(), default=None, help="Export report to a JSON file.")
@click.option("--session", "-s", default=None, help="Filter by session ID.")
@click.option("--from-date", default=None, help="Start date (ISO 8601) for the reporting period.")
@click.option("--to-date", default=None, help="End date (ISO 8601) for the reporting period.")
@click.pass_context
def cli_command(
    ctx: click.Context,
    full: bool,
    output: str | None,
    session: str | None,
    from_date: str | None,
    to_date: str | None,
) -> None:
    """Generate HIPAA Safe Harbor compliance reports."""
    from datetime import datetime

    from phi_redactor.audit.reports import ComplianceReportGenerator
    from phi_redactor.audit.trail import AuditTrail

    config = ctx.obj.get("config")
    if config is None:
        from phi_redactor.config import PhiRedactorConfig
        config = PhiRedactorConfig()

    audit_trail = AuditTrail(audit_dir=str(config.audit_path))
    generator = ComplianceReportGenerator(audit_trail=audit_trail)

    # Parse date filters
    parsed_from = datetime.fromisoformat(from_date) if from_date else None
    parsed_to = datetime.fromisoformat(to_date) if to_date else None

    if output:
        # Export to file
        path = generator.export_report(
            output_path=output,
            from_dt=parsed_from,
            to_dt=parsed_to,
            session_id=session,
        )
        click.echo(f"Compliance report exported to: {path}")
        return

    if full:
        report = generator.generate_report(
            from_dt=parsed_from,
            to_dt=parsed_to,
            session_id=session,
        )
    else:
        report = generator.generate_summary(
            from_dt=parsed_from,
            to_dt=parsed_to,
        )

    if ctx.obj.get("json_output"):
        click.echo(json.dumps(report, indent=2, default=str))
    else:
        _print_human_readable(report, full=full)


def _print_human_readable(report: dict, full: bool = False) -> None:
    """Print the report in a human-readable format."""
    click.secho("=" * 60, fg="cyan")
    click.secho("  PHI Redactor - Compliance Report", fg="cyan", bold=True)
    click.secho("=" * 60, fg="cyan")

    # Summary
    summary = report.get("summary", report)
    click.echo()
    click.secho("Summary:", bold=True)
    click.echo(f"  Total redaction events: {summary.get('total_redaction_events', 0)}")
    click.echo(f"  Unique sessions:        {summary.get('unique_sessions', 0)}")
    click.echo(f"  PHI entities detected:  {summary.get('phi_entities_detected', 0)}")
    click.echo(f"  Categories detected:    {summary.get('categories_detected', 0)}")

    # Compliance status
    status = report.get("compliance_status", {})
    overall = status.get("overall", "unknown")
    color = "green" if overall == "compliant" else ("yellow" if overall == "review_needed" else "white")
    click.echo()
    click.secho(f"Compliance Status: {overall.upper()}", fg=color, bold=True)
    click.echo(f"  {status.get('message', '')}")

    if full and "checks" in status:
        click.echo()
        click.secho("Compliance Checks:", bold=True)
        for name, check in status["checks"].items():
            icon = "PASS" if check["passed"] else "FAIL"
            fg = "green" if check["passed"] else "red"
            click.secho(f"  [{icon}] {name}: {check['detail']}", fg=fg)

    if full and "category_coverage" in report:
        coverage = report["category_coverage"]
        click.echo()
        click.secho("Category Coverage:", bold=True)
        click.echo(f"  {coverage['categories_covered']}/{coverage['total_categories']} categories ({coverage['coverage_percentage']}%)")

    if full and "integrity_verification" in report:
        integrity = report["integrity_verification"]
        fg = "green" if integrity["hash_chain_valid"] else "red"
        click.echo()
        click.secho(f"Audit Trail Integrity: {integrity['status']}", fg=fg, bold=True)

    click.echo()
    click.secho("=" * 60, fg="cyan")
